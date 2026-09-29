#!/usr/bin/env python3
"""
scripts/generate_der_image.py
Gera o diagrama de Entidade-Relacionamento (DER) em imagem PNG de alta resolução.
Salva em BancoDeDados/docs/der.png
"""

import os
from PIL import Image, ImageDraw, ImageFont

def draw_table(draw, x, y, width, title, fields, font_title, font_body):
    header_height = 36
    row_height = 24
    total_height = header_height + len(fields) * row_height + 10

    # Sombra
    draw.rectangle([x + 4, y + 4, x + width + 4, y + total_height + 4], fill="#cbd5e1")
    # Corpo
    draw.rectangle([x, y, x + width, y + total_height], fill="#ffffff", outline="#334155", width=2)
    # Cabeçalho
    draw.rectangle([x, y, x + width, y + header_height], fill="#1e293b")
    draw.text((x + 12, y + 8), title, fill="#ffffff", font=font_title)

    # Campos
    curr_y = y + header_height + 6
    for pk_type, name, data_type in fields:
        color = "#b91c1c" if "PK" in pk_type else ("#0369a1" if "FK" in pk_type else "#334155")
        badge = f"[{pk_type}] " if pk_type else "      "
        text = f"{badge}{name}"
        draw.text((x + 10, curr_y), text, fill=color, font=font_body)
        draw.text((x + width - 90, curr_y), data_type, fill="#64748b", font=font_body)
        curr_y += row_height

    return (x, y, width, total_height)

def main():
    img_width, img_height = 1600, 1000
    img = Image.new("RGB", (img_width, img_height), "#f8fafc")
    draw = ImageDraw.Draw(img)

    # Título do Diagrama
    try:
        font_main = ImageFont.truetype("arialbd.ttf", 26)
        font_sub = ImageFont.truetype("arial.ttf", 16)
        font_title = ImageFont.truetype("arialbd.ttf", 16)
        font_body = ImageFont.truetype("consola.ttf", 14)
    except:
        font_main = font_sub = font_title = font_body = ImageFont.load_default()

    draw.text((50, 30), "DIAGRAMA ENTIDADE-RELACIONAMENTO (DER) - 3ª FORMA NORMAL (3FN)", fill="#0f172a", font=font_main)
    draw.text((50, 68), "Dataset MovieLens 20M - Projeto Banco de Dados Relacional", fill="#475569", font=font_sub)

    # Definição das Tabelas
    tables = {
        "users": (50, 150, 260, "USERS", [
            ("PK", "user_id", "INT")
        ]),
        "ratings": (50, 320, 280, "RATINGS", [
            ("PK,FK", "user_id", "INT"),
            ("PK,FK", "movie_id", "INT"),
            ("", "rating", "NUM(2,1)"),
            ("", "rated_at", "TIMESTAMP")
        ]),
        "movies": (450, 320, 290, "MOVIES", [
            ("PK", "movie_id", "INT"),
            ("", "title", "VARCHAR"),
            ("", "release_year", "SMALLINT")
        ]),
        "movie_links": (450, 150, 290, "MOVIE_LINKS", [
            ("PK,FK", "movie_id", "INT"),
            ("", "imdb_id", "VARCHAR"),
            ("", "tmdb_id", "INT")
        ]),
        "movie_genres": (860, 320, 290, "MOVIE_GENRES", [
            ("PK,FK", "movie_id", "INT"),
            ("PK,FK", "genre_id", "INT")
        ]),
        "genres": (1260, 320, 270, "GENRES", [
            ("PK", "genre_id", "INT"),
            ("UK", "name", "VARCHAR(50)")
        ]),
        "user_movie_tags": (450, 600, 310, "USER_MOVIE_TAGS", [
            ("PK,FK", "user_id", "INT"),
            ("PK,FK", "movie_id", "INT"),
            ("PK,FK", "tag_id", "INT"),
            ("PK", "tagged_at", "TIMESTAMP")
        ]),
        "tags": (900, 600, 280, "TAGS", [
            ("PK", "tag_id", "INT"),
            ("UK", "tag_name", "VARCHAR(255)")
        ])
    }

    boxes = {}
    for key, (x, y, w, title, fields) in tables.items():
        boxes[key] = draw_table(draw, x, y, w, title, fields, font_title, font_body)

    # Conexões / Relacionamentos
    def connect(box1, box2, label=""):
        # Centro das caixas
        x1 = box1[0] + box1[2] // 2
        y1 = box1[1] + box1[3] // 2
        x2 = box2[0] + box2[2] // 2
        y2 = box2[1] + box2[3] // 2
        draw.line([(x1, y1), (x2, y2)], fill="#94a3b8", width=2)

    # Linhas de relacionamento
    # Users -> Ratings
    draw.line([(boxes["users"][0] + 130, boxes["users"][1] + boxes["users"][3]), 
               (boxes["ratings"][0] + 130, boxes["ratings"][1])], fill="#3b82f6", width=2)

    # Movies -> Ratings
    draw.line([(boxes["movies"][0], boxes["movies"][1] + 60), 
               (boxes["ratings"][0] + boxes["ratings"][2], boxes["ratings"][1] + 60)], fill="#3b82f6", width=2)

    # Movies -> Movie_Links (1:1)
    draw.line([(boxes["movies"][0] + 140, boxes["movies"][1]), 
               (boxes["movie_links"][0] + 140, boxes["movie_links"][1] + boxes["movie_links"][3])], fill="#10b981", width=2)

    # Movies -> Movie_Genres (N:M)
    draw.line([(boxes["movies"][0] + boxes["movies"][2], boxes["movies"][1] + 60), 
               (boxes["movie_genres"][0], boxes["movie_genres"][1] + 60)], fill="#6366f1", width=2)

    # Movie_Genres -> Genres
    draw.line([(boxes["movie_genres"][0] + boxes["movie_genres"][2], boxes["movie_genres"][1] + 60), 
               (boxes["genres"][0], boxes["genres"][1] + 60)], fill="#6366f1", width=2)

    # Movies -> User_Movie_Tags
    draw.line([(boxes["movies"][0] + 140, boxes["movies"][1] + boxes["movies"][3]), 
               (boxes["user_movie_tags"][0] + 140, boxes["user_movie_tags"][1])], fill="#ec4899", width=2)

    # Tags -> User_Movie_Tags
    draw.line([(boxes["tags"][0], boxes["tags"][1] + 50), 
               (boxes["user_movie_tags"][0] + boxes["user_movie_tags"][2], boxes["user_movie_tags"][1] + 50)], fill="#ec4899", width=2)

    # Users -> User_Movie_Tags
    draw.line([(boxes["users"][0] + 50, boxes["users"][1] + boxes["users"][3]),
               (boxes["users"][0] + 50, 750),
               (boxes["user_movie_tags"][0], 750)], fill="#ec4899", width=2)

    # Legenda
    legend_y = 880
    draw.rectangle([50, legend_y, 1550, legend_y + 80], fill="#ffffff", outline="#e2e8f0", width=1)
    draw.text((70, legend_y + 15), "LEGENDA DE NORMALIZAÇÃO:", fill="#0f172a", font=font_title)
    draw.text((70, legend_y + 45), "[PK] Chave Primária   |   [FK] Chave Estrangeira   |   [UK] Chave Alternativa Única", fill="#475569", font=font_sub)
    draw.text((800, legend_y + 45), "Conformidade com 1FN, 2FN e 3FN validada sem dependências transitivas nem parciais.", fill="#15803d", font=font_sub)

    out_path = "BancoDeDados/docs/der.png"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    print(f"[+] Imagem gerada com sucesso em: {out_path}")

if __name__ == "__main__":
    main()
