import sqlite3
import json

def get_db():
    return sqlite3.connect('vehicles.db')

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Apaga todas as tabelas existentes
    c.execute('DROP TABLE IF EXISTS maintenance')
    c.execute('DROP TABLE IF EXISTS vehicles')
    
    # Verifica se a coluna color existe
    c.execute("PRAGMA table_info(vehicles)")
    columns = [column[1] for column in c.fetchall()]
    
    # Cria a tabela se não existir
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
    
    # Adiciona a coluna color se não existir
    if 'color' not in columns:
        c.execute('ALTER TABLE vehicles ADD COLUMN color TEXT')

    # Nova tabela para manutenções sem campo next_maintenance_date
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

    # Adiciona a coluna author se não existir
    c.execute("PRAGMA table_info(maintenance)")
    columns = [column[1] for column in c.fetchall()]
    if 'author' not in columns:
        c.execute('ALTER TABLE maintenance ADD COLUMN author TEXT')

    conn.commit()
    conn.close()

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
    """Função melhorada para adicionar veículo com suporte a importação"""
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
    return new_vehicle_id

def get_vehicles():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM vehicles')
    vehicles = [dict(row) for row in c.fetchall()]
    conn.close()
    return vehicles

def update_vehicle(vehicle_id, vehicle_data):
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

def delete_vehicle(vehicle_id):
    conn = get_db()
    c = conn.cursor()
    
    # Primeiro, exclui todas as manutenções associadas ao veículo
    c.execute('DELETE FROM maintenance WHERE vehicle_id = ?', (vehicle_id,))
    
    # Em seguida, exclui o veículo
    c.execute('DELETE FROM vehicles WHERE id = ?', (vehicle_id,))
    
    conn.commit()
    conn.close()

# Funções para gerenciar manutenções
def add_maintenance(maintenance_data):
    conn = get_db()
    c = conn.cursor()
    
    # Adiciona a manutenção sem next_maintenance_date
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
        SET additional_costs = additional_costs + ?
        WHERE id = ?
    ''', (
        maintenance_data['cost'],
        maintenance_data['vehicle_id']
    ))
    
    conn.commit()
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
    conn.commit()
    conn.close()

def delete_maintenance(maintenance_id):
    conn = get_db()
    c = conn.cursor()
    
    # Primeiro obtém os dados da manutenção antes de excluí-la
    c.execute('SELECT vehicle_id, cost FROM maintenance WHERE id = ?', (maintenance_id,))
    maintenance = c.fetchone()
    
    if maintenance:
        vehicle_id, maintenance_cost = maintenance
        
        # Remove a manutenção
        c.execute('DELETE FROM maintenance WHERE id = ?', (maintenance_id,))
        
        # Atualiza os custos adicionais do veículo subtraindo o custo da manutenção
        c.execute('''
            UPDATE vehicles
            SET additional_costs = additional_costs - ?
            WHERE id = ?
        ''', (maintenance_cost, vehicle_id))
        
    conn.commit()
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
