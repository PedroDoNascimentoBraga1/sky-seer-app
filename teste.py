# teste_uv.py
import requests

def test_uv_index_data():
    """
    Testa especificamente a busca por dados de Índice UV na API.
    """
    print("--- Iniciando Teste de Disponibilidade de Índice UV ---")
    
    base_url = "https://archive-api.open-meteo.com/v1/archive"
    
    # Coordenadas do Rio de Janeiro
    lat, lon = -22.9068, -43.1729
    # Data de teste
    day, month = "15", "01"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "1950-01-01",
        "end_date": "2024-12-31", # Usando um ano recente
        "daily": "uv_index_max",
        "timezone": "auto"
    }
    
    print(f"Buscando dados de uv_index_max para Lat: {lat}, Lon: {lon}")
    
    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        print("\n✅ SUCESSO! A API respondeu.")
        print("--- Resposta da API ---")
        # Imprime a resposta completa para análise
        print(data) 
        
        # Análise dos dados recebidos
        daily_data = data.get('daily', {})
        time_list = daily_data.get('time', [])
        uv_list = daily_data.get('uv_index_max', [])

        if not uv_list:
            print("\nANÁLISE: O campo 'uv_index_max' não foi retornado pela API.")
            return

        # Verifica se há algum valor válido na lista (diferente de null)
        valid_points = [uv for uv in uv_list if uv is not None]
        
        print(f"\n--- Análise dos Resultados ---")
        print(f"Total de dias no período: {len(time_list)}")
        print(f"Total de registros de UV recebidos: {len(uv_list)}")
        print(f"Total de registros de UV VÁLIDOS (não nulos): {len(valid_points)}")

        if not valid_points:
            print("\nCONCLUSÃO: A API respondeu, mas não possui dados históricos de Índice UV para esta localização.")
        else:
            print("\nCONCLUSÃO: A API possui dados de Índice UV para esta localização!")


    except Exception as e:
        print(f"\n❌ FALHA: Ocorreu um erro durante a requisição.")
        print(f"Detalhes do erro: {e}")

if __name__ == "__main__":
    test_uv_index_data()