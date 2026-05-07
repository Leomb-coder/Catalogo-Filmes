import os
from logging import exception
from werkzeug.security import generate_password_hash, check_password_hash

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    host = os.environ.get("DB_HOST")
    print("host------------------: ", host)
    conn = psycopg2.connect(
        # host= os.environ.get("DB_HOST"),
        # database= os.environ.get("DB_NAME"),
        # user= os.environ.get("DB_USER"),
        # password= os.environ.get("DB_PASSWORD"),
        host='127.0.0.1',
        database='catalogo_filmes',
        user='postgres',
        password='1234',
    )
    return conn

def consultar_login(email, password):
    # Senha(password) já em hash ^
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(''' SELECT * FROM usuario WHERE email = %s''' , (email,))
        row = cursor.fetchone()

        if row:
            print(f"Usuário {row['nome']} encontrado!")
            if check_password_hash(row['senha'], password):
                return 200
            else:
                return f'Senha inválida'
        else:
            return 'Usuário não encontrado - 404'

    except Exception as ex:
        return str(ex)
    finally:
        cursor.close()
        conn.close()


def cadastrar_usuario(nome, email, senha):
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        senha_hashed = generate_password_hash(senha)

        params = [nome, email, senha_hashed]
        sql = "INSERT INTO usuario (nome, email, senha) VALUES (%s, %s, %s)"
        cursor.execute(sql, params)
        conn.commit()

        return 200

    except Exception as ex:
        conn.rollback() # desfaz em caso de erro
        return str(ex)

    finally:
        cursor.close()
        conn.close()