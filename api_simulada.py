from flask import Flask, request, jsonify
from faker import Faker
import random
import math
from datetime import datetime, timedelta

app = Flask(__name__)
fake = Faker('es_ES')

# Semillas para asegurar que la API siempre devuelva los mismos datos en la misma página
Faker.seed(2026)
random.seed(2026)

# Configuración del entorno de prueba
TOTAL_USERS = 1000
TOTAL_TRANSACTIONS = 5000
VALID_API_KEY = "unl-etl-api-key-2026"

def generate_users(offset, limit):
    """Genera datos de usuarios con PII y errores de calidad."""
    users = []
    for i in range(offset + 1, min(offset + limit + 1, TOTAL_USERS + 1)):
        # Semilla dinámica basada en el ID para consistencia en la paginación
        fake.seed_instance(i) 
        random.seed(i)
        
        email = fake.email()
        if random.random() < 0.05:
            email = None  # 5% de correos nulos (Falla de Completitud)

        users.append({
            "user_id": i,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": email,
            "ip_address": fake.ipv4(),
            "country": fake.country(),
            "registration_date": fake.date_between(start_date='-2y', end_date='today').isoformat()
        })
    return users

def generate_transactions(offset, limit):
    """Genera transacciones financieras con fechas y anomalías."""
    transactions = []
    base_date = datetime.now()
    
    for i in range(offset + 1, min(offset + limit + 1, TOTAL_TRANSACTIONS + 1)):
        fake.seed_instance(i + 10000)
        random.seed(i + 10000)
        
        amount = round(random.uniform(10.0, 1000.0), 2)
        if random.random() < 0.04:
            amount = -amount # 4% de montos negativos (Falla de Validez)
            
        t_date = base_date - timedelta(days=random.randint(0, 5))

        transactions.append({
            "transaction_id": fake.uuid4(),
            "user_id": random.randint(1, TOTAL_USERS),
            "product_category": random.choice(["Electrónica", "Ropa", "Hogar", "Software", "Libros"]),
            "amount": amount,
            "currency": "USD",
            "transaction_date": t_date.strftime("%Y-%m-%d %H:%M:%S"),
            "status": random.choice(["COMPLETED", "COMPLETED", "PENDING", "FAILED"])
        })
    return transactions

def check_auth():
    """Valida la API Key enviada en los headers."""
    api_key = request.headers.get('x-api-key')
    if not api_key or api_key != VALID_API_KEY:
        return False
    return True

def simulate_network_chaos():
    """Motor de caos: simula el comportamiento de una API inestable."""
    prob = random.random()
    if prob < 0.15:
        return jsonify({"error": "Too Many Requests. Rate limit exceeded.", "code": 429}), 429
    elif prob < 0.20:
        return jsonify({"error": "Internal Server Error. Database timeout.", "code": 500}), 500
    return None

@app.route('/api/<entity>', methods=['GET'])
def get_data(entity):
    # 1. Validación de Autenticación
    if not check_auth():
        return jsonify({"error": "Unauthorized. Invalid or missing x-api-key header.", "code": 401}), 401

    # 2. Validación de Entidad
    if entity not in ['users', 'transactions']:
        return jsonify({"error": f"Endpoint '{entity}' not found.", "code": 404}), 404

    # 3. Simulación de Caos (Límites de tasa y caídas de servidor)
    chaos_response = simulate_network_chaos()
    if chaos_response:
        return chaos_response

    # 4. Manejo de Paginación
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 100))
        if limit > 500:
            return jsonify({"error": "Limit cannot exceed 500 records per request.", "code": 400}), 400
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters. Must be integers.", "code": 400}), 400

    offset = (page - 1) * limit
    total_records = TOTAL_USERS if entity == 'users' else TOTAL_TRANSACTIONS
    total_pages = math.ceil(total_records / limit)

    if page > total_pages and total_records > 0:
        return jsonify({"meta": {"current_page": page, "total_pages": total_pages}, "data": []}), 200

    # 5. Generación de Datos
    data = generate_users(offset, limit) if entity == 'users' else generate_transactions(offset, limit)

    return jsonify({
        "meta": {
            "current_page": page,
            "total_pages": total_pages,
            "total_records": total_records,
            "limit": limit
        },
        "data": data
    }), 200

if __name__ == '__main__':
    print("==========================================================")
    print("🚀 API Simulada SABIA-UNL (Diseño de Procesos ETL) Iniciada")
    print("==========================================================")
    print(f"Endpoints disponibles:")
    print(f"  - http://127.0.0.1:5000/api/users")
    print(f"  - http://127.0.0.1:5000/api/transactions")
    print(f"Requisitos de conexión:")
    print(f"  - Header: x-api-key : {VALID_API_KEY}")
    print(f"  - Paginación: ?page=1&limit=100")
    print("NOTA: El motor de caos (429 y 500) está ACTIVO.")
    print("==========================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)