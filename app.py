import os
import uuid

from flask import Flask, request, jsonify, render_template, redirect, url_for
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename
from database import get_connection

app = Flask(__name__)

# ── Upload config ──────────────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'jpeg', 'jpg', 'png'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """Return True only for jpeg/jpg/png files."""
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_upload(file) -> str | None:
    """
    Validate, rename to a UUID-based hash and save the file.
    Returns the relative path stored in the DB (e.g. 'uploads/abc123.jpg'),
    or None if the file is invalid.
    """
    if not file or file.filename == '':
        return None

    original_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if not allowed_file(file.filename):
        return None

    unique_name = f"{uuid.uuid4().hex}.{original_ext}"
    save_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file.save(save_path)

    # Store only the relative path from /static so url_for('static', ...) works
    return f"uploads/{unique_name}"


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "API de catalogo de filmes"}), 200


@app.route('/ping', methods=['GET'])
def ping():
    conn = get_connection()
    conn.close()
    return jsonify({"message": "pong! API Rodando!", "db": str(conn)}), 200


@app.route('/filmes', methods=['GET'])
def listar_filmes():
    sql = "SELECT * FROM filmes"
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql)
        filmes = cursor.fetchall()
        conn.close()
        return render_template("index.html", filmes=filmes)
    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao listar filmes"}), 500


@app.route("/novo", methods=["GET", "POST"])
def novo_filme():
    sql = "INSERT INTO filmes (titulo, genero, ano, url_capa) VALUES (%s, %s, %s, %s)"
    try:
        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            # ── File upload ──────────────────────────────────────────────────
            capa = request.files.get("capa")
            url_capa = save_upload(capa)

            if url_capa is None:
                return jsonify({
                    "message": "Arquivo inválido. Envie uma imagem JPEG, JPG ou PNG."
                }), 400
            # ────────────────────────────────────────────────────────────────

            params = [titulo, genero, ano, url_capa]

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            conn.close()
            return redirect(url_for("listar_filmes"))

        return render_template("novo_filme.html")
    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao cadastrar filme"}), 500


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_filme(id):
    try:
        conn = get_connection()

        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            # ── File upload (optional on edit) ───────────────────────────────
            capa = request.files.get("capa")
            nova_url_capa = save_upload(capa)  # None if no new file sent

            if nova_url_capa:
                # New image uploaded — validate extension
                sql_update = (
                    "UPDATE filmes SET titulo=%s, genero=%s, ano=%s, url_capa=%s "
                    "WHERE id=%s"
                )
                params = [titulo, genero, ano, nova_url_capa, id]
            else:
                # Keep existing image
                sql_update = (
                    "UPDATE filmes SET titulo=%s, genero=%s, ano=%s WHERE id=%s"
                )
                params = [titulo, genero, ano, id]
            # ────────────────────────────────────────────────────────────────

            cursor = conn.cursor()
            cursor.execute(sql_update, params)
            conn.commit()
            conn.close()
            return redirect(url_for("listar_filmes"))

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM filmes WHERE id = %s", [id])
        filme = cursor.fetchone()
        conn.close()

        if filme is None:
            return redirect(url_for("listar_filmes"))
        return render_template("editar_filme.html", filme=filme)
    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao editar filme"}), 500


@app.route("/deletar/<int:id>", methods=["POST"])
def deletar_filme(id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM filmes WHERE id = %s", [id])
        conn.commit()
        conn.close()
        return redirect(url_for("listar_filmes"))
    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao deletar filme"}), 500


if __name__ == '__main__':
    app.run(debug=True)