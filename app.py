import streamlit as st
import sqlite3
import pandas as pd
import io
from database import (
    init_db, add_vehicle, get_vehicles, update_vehicle, delete_vehicle,
    add_maintenance, get_vehicle_maintenance, update_maintenance, delete_maintenance,
    get_all_maintenance_records
)
from fipe_api import get_fipe_brands, get_fipe_models, get_fipe_years, get_fipe_price
from vehicle_manager import save_image
import base64
from io import BytesIO
from datetime import datetime, timedelta
import os
import json
import time  # Adicione esta importação no topo do arquivo
def get_log_files():
    """Retorna lista de arquivos de log disponíveis"""
    log_dir = "logs"
    if os.path.exists(log_dir):
        return [f for f in os.listdir(log_dir) if f.endswith('.log')]
    return []

def read_log_file(filename):
    """Lê e retorna o conteúdo do arquivo de log"""
    try:
        with open(os.path.join("logs", filename), 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Erro ao ler arquivo de log: {str(e)}"

def download_logs():
    """Função para download dos logs"""
    log_files = get_log_files()
    if log_files:
        st.write("### Arquivos de Log Disponíveis")
        for log_file in log_files:
            log_content = read_log_file(log_file)
            st.download_button(
                label=f"📥 Download {log_file}",
                data=log_content,
                file_name=log_file,
                mime="text/plain",
                key=f"download_{log_file}"
            )
    else:
        st.info("Nenhum arquivo de log encontrado.")

def check_password():
    """Verifica a senha para acesso às funcionalidades administrativas"""
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False
        
    if not st.session_state.password_correct:
        password = st.text_input("Digite a senha de administrador", type="password")
        if password == "lipe2008":
            st.session_state.password_correct = True
            st.success("Senha correta!")
            return True
        elif password:
            st.error("Senha incorreta!")
            return False
        return False
    return True

def admin_section():
    """Seção administrativa com funções protegidas por senha"""
    if not check_password():
        return

    tab1, tab2 = st.tabs([
        "📥 Importar/Exportar Veículos",
        "📁 Gerenciar Logs"
    ])
    with tab1:
        st.header("Importar/Exportar Veículos")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Exportar Dados", use_container_width=True):
                json_str = export_vehicles_data()
                if json_str:
                    st.download_button(
                        label="📥 Baixar Backup (JSON)",
                        data=json_str,
                        file_name=f"backup_veiculos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_backup"
                    )
        
        with col2:
            uploaded_file = st.file_uploader(
                "Importar Backup (JSON)",
                type=['json'],
                key="import_vehicles"
            )
            
            if uploaded_file and st.button("📤 Importar Dados", use_container_width=True):
                try:
                    imported = 0
                    data = json.load(uploaded_file)
                    vehicles = data.get('vehicles', [])
                    
                    progress_bar = st.progress(0)
                    for i, vehicle in enumerate(vehicles):
                        # Guarda manutenções antes de adicionar veículo
                        maintenance_records = vehicle.pop('maintenance', [])
                        
                        # Adiciona veículo e obtém novo ID
                        new_vehicle_id = add_vehicle(vehicle)
                        
                        # Adiciona manutenções com o novo ID do veículo
                        for maintenance in maintenance_records:
                            maintenance['vehicle_id'] = new_vehicle_id
                            add_maintenance(maintenance)
                            
                        imported += 1
                        progress_bar.progress((i + 1) / len(vehicles))
                    
                    st.success(f"Importados {imported} veículos com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao importar dados: {str(e)}")

    with tab2:
        st.header("Gerenciar Logs do Sistema")
        download_logs()

def main():
    # Configuração da página para mobile
    st.set_page_config(
        page_title="Gerenciador de Veículos",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'About': 'Gerenciador de Veículos - Versão Mobile'
        }
    )

    # Configurações para melhor experiência mobile
    st.markdown("""
        <style>
        [data-testid="stSidebar"][aria-expanded="true"] {
            max-width: 80%;
            width: 80%;
        }
        .streamlit-expanderHeader {
            font-size: 1em;
        }
        .stButton > button {
            width: 100%;
            border-radius: 20px;
            height: 3em;
        }
        @media (max-width: 640px) {
            .main > div {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
        }
        </style>
    """, unsafe_allow_html=True)
    st._config.set_option('server.address', '0.0.0.0')

    # CSS para melhorar a interface mobile e tornar imagens responsivas
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            height: 50px;
            margin: 5px 0;
        }
        .stSelectbox {
            margin: 10px 0;
        }
        .vehicle-info {
            font-size: 18px !important;
            line-height: 2 !important;
            padding: 10px 0;
        }
        .vehicle-info p {
            margin: 10px 0 !important;
        }
        .delete-button {
            background-color: #ff4b4b !important;
            color: white !important;
            border: none !important;
            padding: 0.5rem !important;
            border-radius: 0.3rem !important;
            cursor: pointer !important;
        }
        .maintenance-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        /* Estilos para imagens responsivas */
        .responsive-img {
            max-width: 100%;
            height: auto;
            margin: 0 auto;
            display: block;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .img-container {
            position: relative;
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            padding: 10px;
        }
        /* Media queries para diferentes tamanhos de tela */
        @media (max-width: 768px) {
            .img-container {
                max-width: 100%;
                padding: 5px;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Gerenciador de Veículos")
    init_db()

    # Adicionar estilo personalizado para o menu lateral
    st.markdown("""
        <style>
        /* Estilo para o menu lateral */
        .sidebar .sidebar-content {
            background-image: linear-gradient(180deg, #2e7bcf 0%, #1565C0 100%);
        }
        
        /* Estilo para os botões do menu */
        .stRadio > label {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin: 5px 0;
            transition: all 0.3s;
        }
        
        .stRadio > label:hover {
            background-color: rgba(255, 255, 255, 0.2);
        }
        
        /* Estilo para o título do menu */
        .sidebar .sidebar-content [data-testid="stMarkdownContainer"] p {
            color: white;
            font-size: 1.2em;
            font-weight: bold;
            padding: 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Menu lateral melhorado
    with st.sidebar:
        st.markdown("### 🚗 Menu do Sistema")
        st.markdown("---")
        
        selected_page = st.radio(
            label="Navegação do Sistema",  # Adicionado label adequado
            options=[
                "📋 Visualizar Veículos",
                "➕ Adicionar Veículo", 
                "⚙️ Administração"
            ],
            key="menu_principal",
            format_func=lambda x: f"{x}",  # Mantém os emojis
            label_visibility="collapsed"  # Esconde o label mas mantém acessibilidade
        )
        
        st.markdown("---")
        st.markdown("##### 🔄 Última atualização:")
        st.text(datetime.now().strftime("%d/%m/%Y %H:%M"))

    # Conteúdo principal baseado na seleção
    if selected_page == "⚙️ Administração":
        admin_section()
    elif selected_page == "➕ Adicionar Veículo":
        add_vehicle_form()
    else:  # Visualizar Veículos
        view_vehicles()

def add_maintenance_form(vehicle_id, maintenance_data=None):
    is_editing = maintenance_data is not None
    
    st.write("### Registrar Manutenção" if not is_editing else "### Editar Manutenção")
    
    with st.form(key=f"maintenance_form_{vehicle_id}"):
        date = st.date_input(
            "Data da Manutenção",
            value=datetime.strptime(maintenance_data['date'], '%Y-%m-%d').date() if is_editing else datetime.now()
        )

        description = st.text_area(
            "Descrição do Serviço",
            value=maintenance_data['description'] if is_editing else ""
        )

        cost = st.number_input(
            "Custo (R$)",
            value=maintenance_data['cost'] if is_editing else 0.0,
            min_value=0.0,
            step=10.0,
            format="%.2f"
        )

        mileage = st.number_input(
            "Quilometragem",
            value=maintenance_data['mileage'] if is_editing else 0,
            min_value=0
        )

        next_date = st.date_input(
            "Próxima Manutenção",
            value=datetime.strptime(maintenance_data['next_maintenance_date'], '%Y-%m-%d').date() if is_editing and maintenance_data['next_maintenance_date'] else (datetime.now() + timedelta(days=180)).date()
        )

        # Seleção do autor simplificada
        author = st.selectbox(
            "Autor da Manutenção",
            ["Antonio", "Fernando"],
            key=f"author_{vehicle_id}",
            index=0 if not is_editing else (
                0 if maintenance_data['author'] == "Antonio" else 1
            )
        )

        submit = st.form_submit_button("Salvar Manutenção")

        if submit:
            try:
                maintenance_info = {
                    'vehicle_id': vehicle_id,
                    'date': date.strftime('%Y-%m-%d'),
                    'description': description,
                    'cost': cost,
                    'mileage': mileage,
                    'next_maintenance_date': next_date.strftime('%Y-%m-%d'),
                    'author': author
                }

                if is_editing:
                    update_maintenance(maintenance_data['id'], maintenance_info)
                    st.success("Manutenção atualizada com sucesso!")
                else:
                    add_maintenance(maintenance_info)
                    st.success("Manutenção registrada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao {'atualizar' if is_editing else 'registrar'} manutenção: {str(e)}")

def view_maintenance_history(vehicle_id):
    maintenance_records = get_vehicle_maintenance(vehicle_id)
    
    # Inicializar o estado de confirmação de exclusão se não existir
    if 'delete_confirmation' not in st.session_state:
        st.session_state.delete_confirmation = None
    
    # Botão para adicionar nova manutenção
    if st.button("➕ Nova Manutenção", key=f"add_maintenance_{vehicle_id}"):
        st.session_state.show_maintenance_form = True
        st.session_state.current_vehicle = vehicle_id
        
    # Mostrar formulário de nova manutenção
    if getattr(st.session_state, 'show_maintenance_form', False) and getattr(st.session_state, 'current_vehicle', None) == vehicle_id:
        with st.container():
            date = st.date_input("Data da Manutenção")
            description = st.text_area("Descrição do Serviço")
            cost = st.number_input("Custo (R$)", min_value=0.0, step=10.0, format="%.2f")
            mileage = st.number_input("Quilometragem", min_value=0)
            author = st.selectbox("Autor da Manutenção", 
                                ["Antonio", "Fernando"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar", key=f"save_maint_{vehicle_id}"):
                    try:
                        maintenance_info = {
                            'vehicle_id': vehicle_id,
                            'date': date.strftime('%Y-%m-%d'),
                            'description': description,
                            'cost': cost,
                            'mileage': mileage,
                            'author': author
                        }
                        add_maintenance(maintenance_info)
                        st.success("Manutenção registrada com sucesso!")
                        st.session_state.show_maintenance_form = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao registrar manutenção: {str(e)}")

            with col2:
                if st.button("❌ Cancelar", key=f"cancel_add_{vehicle_id}"):
                    st.session_state.show_maintenance_form = False
                    st.rerun()

    # Exibir manutenções existentes
    if maintenance_records:
        st.markdown("### Histórico de Manutenções")
        for record in maintenance_records:
            st.markdown("---")  # Separador entre registros
            st.markdown(f"### 📅 {record['date']} - {record['description'][:30]}...")
            st.markdown("""
                <div class="maintenance-card">
                    <p><strong>Autor:</strong> {author}</p>
                    <p><strong>Descrição:</strong> {description}</p>
                    <p><strong>Custo:</strong> R$ {cost:.2f}</p>
                    <p><strong>Quilometragem:</strong> {mileage} km</p>
                </div>
            """.format(
                author=record['author'],
                description=record['description'],
                cost=record['cost'],
                mileage=record['mileage']
            ), unsafe_allow_html=True)

            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🗑️", key=f"delete_maint_{record['id']}"):
                    st.session_state.delete_confirmation = record['id']

            if st.session_state.delete_confirmation == record['id']:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("⚠️ Confirmar", key=f"confirm_delete_maint_{record['id']}"):
                        delete_maintenance(record['id'])
                        st.success("Manutenção excluída com sucesso!")
                        st.session_state.delete_confirmation = None
                        st.rerun()
                with col2:
                    if st.button("❌ Cancelar", key=f"cancel_delete_maint_{record['id']}"):
                        st.session_state.delete_confirmation = None
                        st.rerun()
    else:
        st.info("Nenhuma manutenção registrada para este veículo.")

def add_vehicle_form(vehicle_data=None):
    is_editing = vehicle_data is not None
    st.header("Editar Veículo" if is_editing else "Adicionar Novo Veículo")

    with st.container():
        brands = get_fipe_brands()
        selected_brand = st.selectbox(
            "Marca do Veículo",
            options=brands['codigo'].tolist(),
            format_func=lambda x: brands[brands['codigo'] == x]['nome'].iloc[0],
            index=0 if not is_editing else next((i for i, row in brands.iterrows() if row['nome'] == vehicle_data['brand']), 0)
        )

        models = get_fipe_models(selected_brand)
        selected_model = st.selectbox(
            "Modelo do Veículo",
            options=models['codigo'].tolist(),
            format_func=lambda x: models[models['codigo'] == x]['nome'].iloc[0],
            index=0 if not is_editing else next((i for i, row in models.iterrows() if row['nome'] == vehicle_data['model']), 0)
        )

        years = get_fipe_years(selected_brand, selected_model)
        selected_year = st.selectbox(
            "Ano do Veículo",
            options=years['codigo'].tolist(),
            format_func=lambda x: years[years['codigo'] == x]['nome'].iloc[0],
            index=0 if not is_editing else next((i for i, row in years.iterrows() if row['nome'] == vehicle_data['year']), 0)
        )

        color = st.text_input(
            "Cor do Veículo",
            value=vehicle_data.get('color', '') if is_editing else ""
        )

        purchase_price = st.number_input(
            "Valor de Aquisição (R$)",
            min_value=0.0,
            step=100.0,
            format="%.2f",
            value=vehicle_data['purchase_price'] if is_editing else 0.0
        )

        additional_costs = st.number_input(
            "Custos Adicionais (R$)",
            min_value=0.0,
            step=100.0,
            format="%.2f",
            value=vehicle_data['additional_costs'] if is_editing else 0.0
        )

        uploaded_file = st.file_uploader(
            "Foto do Veículo",
            type=['jpg', 'jpeg', 'png']
        )

        try:
            fipe_data = get_fipe_price(selected_brand, selected_model, selected_year)
            fipe_price = float(fipe_data['Valor'].replace('R$ ', '').replace('.', '').replace(',', '.'))
            st.info(f"Valor FIPE: R$ {fipe_price:,.2f}")
        except Exception as e:
            st.error(f"Erro ao obter valor FIPE: {str(e)}")
            fipe_price = 0.0

        button_text = "💾 Salvar Alterações" if is_editing else "💾 Adicionar Veículo"
        if st.button(button_text, use_container_width=True, type="primary"):
            try:
                # Mantém a imagem existente se não houver upload de nova imagem
                if is_editing:
                    image_data = vehicle_data['image_data']
                    if uploaded_file:
                        image_bytes = uploaded_file.getvalue()
                        image_data = base64.b64encode(image_bytes).decode()
                else:
                    image_data = None
                    if uploaded_file:
                        image_bytes = uploaded_file.getvalue()
                        image_data = base64.b64encode(image_bytes).decode()

                total_cost = purchase_price + additional_costs
                fipe_difference = fipe_price - total_cost

                vehicle_info = {
                    'brand': brands[brands['codigo'] == selected_brand]['nome'].iloc[0],
                    'model': models[models['codigo'] == selected_model]['nome'].iloc[0],
                    'year': years[years['codigo'] == selected_year]['nome'].iloc[0],
                    'color': color,
                    'purchase_price': purchase_price,
                    'additional_costs': additional_costs,
                    'fipe_price': fipe_price,
                    'image_data': image_data
                }

                if is_editing:
                    update_vehicle(vehicle_data['id'], vehicle_info)
                    st.success("✅ Veículo atualizado com sucesso!")
                    st.session_state.editing_vehicle = None
                else:
                    add_vehicle(vehicle_info)
                    st.success("✅ Veículo adicionado com sucesso!")
                st.balloons()
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao {'atualizar' if is_editing else 'adicionar'} veículo: {str(e)}")

def export_maintenance_report():
    records = get_all_maintenance_records()
    if records:
        df = pd.DataFrame(records)
        df = df[[
            'date', 'brand', 'model', 'year', 'description',
            'cost', 'mileage'
        ]]
        df.columns = [
            'Data', 'Marca', 'Modelo', 'Ano', 'Descrição',
            'Custo', 'Quilometragem'
        ]
        
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="📥 Exportar Relatório de Manutenções",
            data=csv,
            file_name="relatorio_manutencoes.csv",
            mime="text/csv"
        )
    else:
        st.info("Não há registros de manutenção para exportar.")

def export_vehicles_data():
    """Função para exportar dados de todos os veículos e suas manutenções"""
    vehicles = get_vehicles()
    if not vehicles:
        st.info("Não há veículos para exportar.")
        return
    
    # Adiciona manutenções para cada veículo
    for vehicle in vehicles:
        vehicle['maintenance'] = get_vehicle_maintenance(vehicle['id'])
        
    export_data = {
        'vehicles': vehicles,
        'export_date': datetime.now().isoformat()
    }
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    return json_str

def import_vehicles_data():
    """Função para importar dados de veículos"""
    uploaded_file = st.file_uploader(
        "Importar Veículos (JSON)",
        type=['json'],
        key="import_vehicles"
    )
    if uploaded_file:
        try:
            data = pd.read_json(uploaded_file)
            for _, row in data.iterrows():
                vehicle_data = row.to_dict()
                add_vehicle(vehicle_data)
            st.success(f"Importados {len(data)} veículos com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao importar veículos: {str(e)}")

def view_vehicles():
    st.header("Veículos Cadastrados")
    
    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("📊", help="Exportar Relatório de Manutenções", key="export_report"):
            export_maintenance_report()
    
    vehicles = get_vehicles()
    if not vehicles:
        st.warning("Nenhum veículo cadastrado.")
        return
    
    st.subheader(f"Total de veículos: {len(vehicles)}")
    for vehicle in vehicles:
        with st.expander(f"{vehicle['brand']} {vehicle['model']} ({vehicle['year']})"):
            if st.session_state.editing_vehicle == vehicle['id']:
                add_vehicle_form(vehicle)
                if st.button("❌ Cancelar Edição", key=f"cancel_{vehicle['id']}", type="primary"):
                    st.session_state.editing_vehicle = None
                    st.rerun()
            else:
                if vehicle['image_data']:
                    try:
                        image_bytes = base64.b64decode(vehicle['image_data'])
                        with st.container():
                            st.markdown('<div class="img-container">', unsafe_allow_html=True)
                            st.image(
                                image_bytes,
                                width=400,
                                output_format="PNG",
                                caption=f"{vehicle['brand']} {vehicle['model']}",
                                clamp=True
                            )
                            st.markdown('</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Erro ao carregar imagem: {str(e)}")

                total_cost = vehicle['purchase_price'] + vehicle['additional_costs']
                difference = vehicle['fipe_price'] - total_cost

                st.markdown(f"""
                    <div class="vehicle-info">
                    <p>🎨 <strong>Cor:</strong> {vehicle.get('color', 'Não informada')}</p>
                    <p>📊 <strong>Valor de Aquisição:</strong> R$ {vehicle['purchase_price']:.2f}</p>
                    <p>💰 <strong>Custos Adicionais:</strong> R$ {vehicle['additional_costs']:.2f}</p>
                    <p>💵 <strong>Valor Total:</strong> R$ {total_cost:.2f}</p>
                    <p>🚗 <strong>Valor FIPE:</strong> R$ {vehicle['fipe_price']:.2f}</p>
                    <p>📈 <strong>Diferença FIPE:</strong> R$ {difference:.2f}</p>
                    </div>
                """, unsafe_allow_html=True)

                if difference > 0:
                    st.success("✅ Valor positivo em relação à FIPE")
                else:
                    st.error("❌ Valor negativo em relação à FIPE")

                st.subheader("📝 Histórico de Manutenções")
                view_maintenance_history(vehicle['id'])

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Editar", key=f"edit_{vehicle['id']}", type="primary"):
                        st.session_state.editing_vehicle = vehicle['id']
                        st.rerun()
                with col2:
                    if st.button(f"🗑️ Excluir", key=f"delete_{vehicle['id']}", type="primary"):
                        st.session_state.delete_vehicle_confirmation = vehicle['id']

            if st.session_state.delete_vehicle_confirmation == vehicle['id']:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"⚠️ Confirmar", key=f"confirm_{vehicle['id']}", type="primary"):
                        delete_vehicle(vehicle['id'])
                        st.success("Veículo excluído com sucesso!")
                        st.session_state.delete_vehicle_confirmation = None
                        st.rerun()
                with col2:
                    if st.button("❌ Cancelar", key=f"cancel_delete_{vehicle['id']}", type="primary"):
                        st.session_state.delete_vehicle_confirmation = None
                        st.rerun()

if __name__ == "__main__":
    main()
