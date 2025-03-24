import sqlite3
import json
import os
import shutil
from datetime import datetime
from cache_manager import (
    save_vehicles_to_cache, load_vehicles_from_cache,
    update_vehicle_in_cache, delete_vehicle_from_cache
)

BACKUP_DIR = "data/backups"
CURRENT_DB = "vehicles.db"

def ensure_backup_dir():
    """Garante que o diretório de backup existe"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)

def create_backup():
    """Cria backup do banco de dados atual"""
    ensure_backup_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'vehicles_backup_{timestamp}.db')
    
    if os.path.exists(CURRENT_DB):
        shutil.copy2(CURRENT_DB, backup_file)
        
        # Mantém apenas os 5 backups mais recentes
        backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')])
        if len(backups) > 5:
            for old_backup in backups[:-5]:
                os.remove(os.path.join(BACKUP_DIR, old_backup))

def restore_latest_backup():
    """Restaura o backup mais recente se o banco atual não existir"""
    if not os.path.exists(CURRENT_DB) and os.path.exists(BACKUP_DIR):
        backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')])
        if backups:
            latest_backup = os.path.join(BACKUP_DIR, backups[-1])
            shutil.copy2(latest_backup, CURRENT_DB)
            return True
    return False

def get_db():
    return sqlite3.connect('vehicles.db')

def init_db():
    """Inicializa o banco de dados com suporte a backup"""
    # Tenta restaurar backup se necessário
    restore_latest_backup()
    
    conn = get_db()
    c = conn.cursor()
    
    # Criar tabela de veículos se não existir
    c.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year TEXT NOT NULL,
            color TEXT,
            purchase_price REAL NOT NULL,
            additional_costs REAL NOT NULL,
            fipe_price REAL NOT NULL,
            image_data TEXT
        )
    ''')

    # Criar tabela de manutenções se não existir
    c.execute('''
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            cost REAL NOT NULL,
            mileage INTEGER,
            author TEXT NOT NULL,  
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
    ''')

    conn.commit()
    conn.close()
    
    # Cria novo backup após inicialização
    create_backup()

def check_vehicle_exists(brand, model, year, color):
    """Verifica se um veículo com as mesmas características já existe"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM vehicles 
        WHERE brand = ? AND model = ? AND year = ? AND color = ?
    ''', (brand, model, year, color))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def add_vehicle(vehicle_data):
    """Adiciona veículo e atualiza cache"""
    conn = get_db()
    c = conn.cursor()
    
    # Remove id e maintenance se existirem (para importação)
    vehicle_data.pop('id', None)
    vehicle_data.pop('maintenance', None)
    
    # Garante que todos os campos necessários existam
    required_fields = ['brand', 'model', 'year', 'color', 'purchase_price', 
                      'additional_costs', 'fipe_price', 'image_data']
    
    for field in required_fields:
        if field not in vehicle_data:
            vehicle_data[field] = None

    # Verifica se já existe veículo idêntico
    if check_vehicle_exists(
        vehicle_data['brand'],
        vehicle_data['model'],
        vehicle_data['year'],
        vehicle_data['color']
    ):
        # Modifica o nome adicionando um sufixo
        suffix = 1
        original_model = vehicle_data['model']
        while check_vehicle_exists(
            vehicle_data['brand'],
            f"{original_model} ({suffix})",
            vehicle_data['year'],
            vehicle_data['color']
        ):
            suffix += 1
        vehicle_data['model'] = f"{original_model} ({suffix})"
            
    c.execute('''
        INSERT INTO vehicles (brand, model, year, color, purchase_price, 
                            additional_costs, fipe_price, image_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        vehicle_data['brand'],
        vehicle_data['model'],
        vehicle_data['year'],
        vehicle_data['color'],
        vehicle_data['purchase_price'],
        vehicle_data['additional_costs'],
        vehicle_data['fipe_price'],
        vehicle_data['image_data']
    ))
    
    # Retorna o ID do veículo inserido
    new_vehicle_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # Após inserir, atualiza o cache
    vehicles = get_vehicles()
    vehicle_data['id'] = new_vehicle_id
    vehicles.append(vehicle_data)
    save_vehicles_to_cache(vehicles)
    
    return new_vehicle_id

def get_vehicles():
    """Busca veículos primeiro no cache, depois no banco"""
    cached_vehicles = load_vehicles_from_cache()
    if (cached_vehicles is not None):
        return cached_vehicles

    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM vehicles')
    vehicles = [dict(row) for row in c.fetchall()]
    conn.close()
    
    # Salva no cache
    save_vehicles_to_cache(vehicles)
    return vehicles

def update_vehicle(vehicle_id, vehicle_data):
    """Atualiza veículo e cache"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE vehicles
        SET brand=?, model=?, year=?, color=?, purchase_price=?, additional_costs=?, fipe_price=?, image_data=?
        WHERE id=?
    ''', (
        vehicle_data['brand'],
        vehicle_data['model'],
        vehicle_data['year'],
        vehicle_data['color'],
        vehicle_data['purchase_price'],
        vehicle_data['additional_costs'],
        vehicle_data['fipe_price'],
        vehicle_data['image_data'],
        vehicle_id
    ))
    conn.commit()
    conn.close()
    
    # Atualiza o cache
    vehicle_data['id'] = vehicle_id
    update_vehicle_in_cache(vehicle_id, vehicle_data)

def delete_vehicle(vehicle_id):
    """Remove veículo e atualiza cache"""
    conn = get_db()
    c = conn.cursor()
    
    # Primeiro, exclui todas as manutenções associadas ao veículo
    c.execute('DELETE FROM maintenance WHERE vehicle_id = ?', (vehicle_id,))
    
    # Em seguida, exclui o veículo
    c.execute('DELETE FROM vehicles WHERE id = ?', (vehicle_id,))
    
    conn.commit()
    conn.close()
    
    # Remove do cache
    delete_vehicle_from_cache(vehicle_id)

# Funções para gerenciar manutenções
def add_maintenance(maintenance_data):
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Inicia uma transação
        c.execute('BEGIN TRANSACTION')
        
        # Adiciona a manutenção
        c.execute('''
            INSERT INTO maintenance (vehicle_id, date, description, cost, mileage, author)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            maintenance_data['vehicle_id'],
            maintenance_data['date'],
            maintenance_data['description'],
            maintenance_data['cost'],
            maintenance_data['mileage'],
            maintenance_data['author']
        ))
        
        # Atualiza os custos adicionais do veículo
        c.execute('''
            UPDATE vehicles 
            SET additional_costs = (
                SELECT COALESCE(SUM(cost), 0)
                FROM maintenance
                WHERE vehicle_id = ?
            )
            WHERE id = ?
        ''', (maintenance_data['vehicle_id'], maintenance_data['vehicle_id']))

        # Atualiza o cache
        c.execute('SELECT * FROM vehicles WHERE id = ?', (maintenance_data['vehicle_id'],))
        vehicle = dict(c.fetchone())
        update_vehicle_in_cache(maintenance_data['vehicle_id'], vehicle)
        
        # Confirma a transação
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_vehicle_maintenance(vehicle_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM maintenance WHERE vehicle_id = ? ORDER BY date DESC', (vehicle_id,))
    maintenance_records = [dict(row) for row in c.fetchall()]
    conn.close()
    return maintenance_records

def update_maintenance(maintenance_id, maintenance_data):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('BEGIN TRANSACTION')

        # Atualiza a manutenção
        c.execute('''
            UPDATE maintenance
            SET date=?, description=?, cost=?, mileage=?, author=?
            WHERE id=?
        ''', (
            maintenance_data['date'],
            maintenance_data['description'],
            maintenance_data['cost'],
            maintenance_data['mileage'],
            maintenance_data['author'],
            maintenance_id
        ))

        # Recalcula custos adicionais do veículo
        c.execute('''
            UPDATE vehicles 
            SET additional_costs = (
                SELECT COALESCE(SUM(cost), 0)
                FROM maintenance
                WHERE vehicle_id = ?
            )
            WHERE id = ?
        ''', (maintenance_data['vehicle_id'], maintenance_data['vehicle_id']))

        # Atualiza o cache
        c.execute('SELECT * FROM vehicles WHERE id = ?', (maintenance_data['vehicle_id'],))
        vehicle = dict(c.fetchone())
        update_vehicle_in_cache(maintenance_data['vehicle_id'], vehicle)
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_maintenance(maintenance_id):
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Inicia uma transação
        c.execute('BEGIN TRANSACTION')
        
        # Obtém o vehicle_id antes de deletar
        c.execute('SELECT vehicle_id FROM maintenance WHERE id = ?', (maintenance_id,))
        result = c.fetchone()
        
        if result:
            vehicle_id = result[0]
            
            # Remove a manutenção
            c.execute('DELETE FROM maintenance WHERE id = ?', (maintenance_id,))
            
            # Recalcula o total de custos adicionais
            c.execute('''
                UPDATE vehicles 
                SET additional_costs = (
                    SELECT COALESCE(SUM(cost), 0)
                    FROM maintenance
                    WHERE vehicle_id = ?
                )
                WHERE id = ?
            ''', (vehicle_id, vehicle_id))
            
        # Confirma a transação
        c.execute('COMMIT')
        conn.commit()
    except Exception as e:
        c.execute('ROLLBACK')
        raise e
    finally:
        conn.close()

def get_all_maintenance_records():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT m.*, v.brand, v.model, v.year
        FROM maintenance m
        JOIN vehicles v ON m.vehicle_id = v.id
        ORDER BY m.date DESC
    ''')
    maintenance_records = [dict(row) for row in c.fetchall()]
    conn.close()
    return maintenance_records

def get_vehicle_by_details(brand, model, year, color):
    """Retorna um veículo específico baseado nos detalhes"""
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT * FROM vehicles 
        WHERE brand = ? AND model = ? AND year = ? AND color = ?
    ''', (brand, model, year, color))
    vehicle = c.fetchone()
    conn.close()
    return dict(vehicle) if vehicle else None

def get_maintenance_totals_by_author():
    """Retorna o total de manutenções por autor"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT author, SUM(cost) as total
        FROM maintenance
        GROUP BY author
    ''')
    results = c.fetchall()
    conn.close()
    
    # Converte para dicionário
    totals = {}
    for author, total in results:
        totals[author] = total
    
    return totals
