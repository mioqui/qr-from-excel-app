# Requiere: pip install streamlit pandas qrcode pillow

import streamlit as st
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
import tempfile
import zipfile
import json

# Fuente personalizada o por defecto
font_path = os.path.join("fonts", "arial.ttf")
fuente = ImageFont.truetype(font_path, 50) if os.path.exists(font_path) else ImageFont.load_default()

st.title("Generador de QRs desde Excel v1.0")


uploaded_file = st.file_uploader("📥 Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("✅ Excel cargado correctamente.")
    st.dataframe(df)

    codigos = df.index.tolist()
    seleccion = st.selectbox("🔍 Vista previa QR para la fila:", codigos)

    if seleccion is not None:
        fila = df.loc[seleccion]
        
        # Texto visible sobre el QR: Nivel | Veta | Tajo
        texto = f"{fila['Nivel']} | {fila['Veta']} | {fila['Tajo']}"
        
        # Generar QR con todos los datos en formato JSON
        json_str = json.dumps({k: str(v) for k, v in fila.items()}, ensure_ascii=False)
        qr = qrcode.make(json_str).convert("RGB")

        # Medidas del texto
        draw_temp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        bbox = draw_temp.textbbox((0, 0), texto, font=fuente)
        ancho_texto = bbox[2] - bbox[0]
        alto_texto = bbox[3] - bbox[1]
        ancho_qr, alto_qr = qr.size
        altura_total = alto_qr + alto_texto + 40

        # Composición de imagen final
        img_final = Image.new("RGB", (ancho_qr, altura_total), "white")
        draw = ImageDraw.Draw(img_final)
        x_texto = (ancho_qr - ancho_texto) // 2
        draw.text((x_texto, 10), texto, fill="black", font=fuente)
        img_final.paste(qr, (0, alto_texto + 20))

        st.image(img_final, caption="Vista previa del QR", use_container_width=False)

    if st.button("📦 Generar ZIP con QRs"):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "qrs")
            os.makedirs(output_dir, exist_ok=True)
            zip_path = os.path.join(temp_dir, "QRs.zip")

            for i, row in df.iterrows():
                texto = f"{row['Nivel']} | {row['Veta']} | {row['Tajo']}"
                json_str = json.dumps({k: str(v) for k, v in row.items()}, ensure_ascii=False)
                qr = qrcode.make(json_str).convert("RGB")
                draw_temp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
                bbox = draw_temp.textbbox((0, 0), texto, font=fuente)
                ancho_texto = bbox[2] - bbox[0]
                alto_texto = bbox[3] - bbox[1]
                ancho_qr, alto_qr = qr.size
                altura_total = alto_qr + alto_texto + 40
                img_final = Image.new("RGB", (ancho_qr, altura_total), "white")
                draw = ImageDraw.Draw(img_final)
                x_texto = (ancho_qr - ancho_texto) // 2
                draw.text((x_texto, 10), texto, fill="black", font=fuente)
                img_final.paste(qr, (0, alto_texto + 20))

                # Nombre del archivo = Tajo
                nombre_base = str(row["Tajo"]).strip().replace("/", "-").replace("\\", "-")
                nombre_archivo = nombre_base if nombre_base else f"QR_{i}"
                img_path = os.path.join(output_dir, f"{nombre_archivo}.png")
                img_final.save(img_path)

            with zipfile.ZipFile(zip_path, "w") as zipf:
                for file in os.listdir(output_dir):
                    zipf.write(os.path.join(output_dir, file), arcname=file)

            with open(zip_path, "rb") as f:
                st.download_button("⬇️ Descargar ZIP con QRs", f, file_name="QRs.zip", mime="application/zip")
