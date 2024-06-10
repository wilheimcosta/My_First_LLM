import requests
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import tkinter.font as tk_font  # Importe o módulo tkinter.font

# Função para obter a hora UTC atual no formato YYYYMMDDHH
def get_utc_date():
    now = datetime.utcnow()
    return now.strftime('%Y%m%d%H')

# Função para obter a hora UTC de 24 horas atrás no formato YYYYMMDDHH
def get_utc_date_minus_24_hours():
    now = datetime.utcnow() - timedelta(hours=24)
    return now.strftime('%Y%m%d%H')

# Função para formatar a data no formato dd/mm/yyyy - hh:mm:ss UTC
def format_date(date_string, include_seconds=True):
    date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    formatted_date = date.strftime('%d/%m/%Y - %H:%M')
    if include_seconds:
        formatted_date += ':' + date.strftime('%S')
    return formatted_date + ' UTC'

# Função para verificar se a hora está dentro do intervalo especificado
def is_within_time_range(recebimento, validade_inicial, minutes_before, minutes_after):
    recebimento_datetime = datetime.strptime(recebimento, '%Y-%m-%d %H:%M:%S')
    validade_inicial_datetime = datetime.strptime(validade_inicial, '%Y-%m-%d %H:%M:%S')
    validade_inicial_datetime -= timedelta(minutes=minutes_before)
    validade_final_datetime = datetime.strptime(validade_inicial, '%Y-%m-%d %H:%M:%S')
    validade_final_datetime += timedelta(minutes=minutes_after)
    return validade_inicial_datetime <= recebimento_datetime < validade_final_datetime

# Função para obter e exibir os dados METAR e SYNOP
def update_data():
    global metar_table, treeview

    # Limpa a árvore de exibição
    treeview.delete(*treeview.get_children())

    # Obtenha a hora UTC atual e a hora UTC de 24 horas atrás
    current_utc_date = get_utc_date()
    utc_date_minus_24_hours = get_utc_date_minus_24_hours()

    # Define a URL para METAR e SYNOP
    api_key = 'povFnv4k9aMAGTXnxNVjXfj6cViT0Pqy7RGNUyzM'
    metar_url = f"https://api-redemet.decea.mil.br/mensagens/metar/SBMQ?api_key={api_key}&data_ini={utc_date_minus_24_hours}&data_fim={current_utc_date}"
    synop_url = f"https://api-redemet.decea.mil.br/mensagens/synop?api_key={api_key}&estacao=82099&data_ini={utc_date_minus_24_hours}&data_fim={current_utc_date}"

    # Obtenha os dados METAR e SYNOP
    metar_response = requests.get(metar_url)
    synop_response = requests.get(synop_url)

    # Verifique se as solicitações foram bem-sucedidas
    if metar_response.status_code == 200 and synop_response.status_code == 200:
        metar_data = metar_response.json()
        synop_data = synop_response.json()

        # Ordene os dados METAR por horário em ordem decrescente
        metar_data['data']['data'].sort(key=lambda x: x['validade_inicial'], reverse=True)

        # Ordene os dados SYNOP por horário em ordem decrescente
        synop_data['data']['data'].sort(key=lambda x: x['validade_inicial'], reverse=True)

        # Itere sobre o array de dados METAR e crie uma representação de tabela
        metar_table = []
        for metar_item in metar_data['data']['data']:
            metar_row = []
            metar_row.append(metar_item['id_localidade'])
            metar_row.append(format_date(metar_item['validade_inicial'], include_seconds=False))

            # Formata a mensagem METAR para negrito e verde se começar com "AAXX"
            mens = metar_item['mens']
            if mens.startswith("AAXX"):
                mens = f"**<font color='green'>{mens}</font>**"
            metar_row.append(mens)

            metar_row.append(format_date(metar_item['recebimento']))

            # Adicione a mensagem SYNOP correspondente à linha METAR
            synop_message = ''
            for synop_item in synop_data['data']['data']:
                synop_datetime = synop_item['mens'][5:9]
                synop_day = synop_datetime[:2]
                synop_hour = synop_datetime[2:]
                metar_date = metar_row[1].split(" - ")[0]
                metar_hour = metar_row[1].split(" - ")[1][:2]
                if metar_date.split("/")[0] == synop_day and metar_hour == synop_hour:
                    synop_message = synop_item['mens']
                    break
            metar_row.append(synop_message)  # Adiciona a mensagem SYNOP à linha METAR

            metar_table.append(metar_row)

        # Adiciona os dados à árvore de exibição
        for row in metar_table:
            treeview.insert("", tk.END, values=row)

        # Salva os dados em um arquivo "Metar-Synop.txt"
        with open("Metar-Synop.txt", "w", encoding="utf-8") as arquivo:
            for row in metar_table:
                arquivo.write(f"{row[0]} - {row[1]} - {row[2]} - {row[3]}\n")  # Escreve a linha METAR
                if row[4]:  # Se houver mensagem SYNOP
                    arquivo.write(f"SYNOP: {row[4]}\n")  # Escreve a mensagem SYNOP em uma nova linha

    else:
        messagebox.showerror("Erro", "Erro ao obter dados da API.")

# Cria a janela principal
window = tk.Tk()
window.title("Check-list METAR e SYNOP")

# Define o tema ttk para "clam"
style = ttk.Style()
style.theme_use('clam')

# Define a fonte padrão para a janela
style.configure('.', font=("CourrierNew", 8))

# Cria a árvore de exibição
treeview = ttk.Treeview(window, columns=("Estação", "Validade Inicial", "Mensagem", "Transmissão", "SYNOP"), show="headings")

# Define as colunas da árvore de exibição
treeview.column("Estação", anchor=tk.CENTER, width=30)  # Largura fixa para a coluna "Estação"
treeview.column("Validade Inicial", anchor=tk.CENTER, width=100)  # Largura fixa
treeview.column("Mensagem", anchor=tk.W, width=300)  # Largura fixa
treeview.column("Transmissão", anchor=tk.CENTER, width=150)  # Largura fixa
treeview.column("SYNOP", anchor=tk.W, width=300)  # Largura fixa

# Define os cabeçalhos das colunas
treeview.heading("Estação", text="Estação")
treeview.heading("Validade Inicial", text="Validade Inicial")
treeview.heading("Mensagem", text="Mensagem")
treeview.heading("Transmissão", text="Transmissão")
treeview.heading("SYNOP", text="SYNOP")  # Adiciona cabeçalho para a coluna SYNOP

# Adiciona a árvore de exibição à janela
treeview.pack(fill=tk.BOTH, expand=True)

# Configura os estilos das linhas da árvore para melhor legibilidade
style.configure("Treeview", background="white", foreground="black", fieldbackground="white", rowheight=50)
style.map("Treeview", background=[("selected", "blue")])

# Cria o botão "Atualizar"
update_button = ttk.Button(window, text="Atualizar", command=update_data)
update_button.pack(pady=10)

# Espaçamento entre widgets
window.grid_rowconfigure(0, weight=1)
window.grid_columnconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=0)
window.grid_columnconfigure(0, weight=1)

# Chama a função para atualizar os dados inicialmente
update_data()

# Inicia o loop principal da janela
window.mainloop()