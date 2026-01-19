import streamlit as st

# Configuración de página
st.set_page_config(page_title="Gestión de Neumáticos", page_icon="🛞", layout="centered")

# Estilos CSS
st.markdown("""
<style>
.blue-line { border-top: 3px solid #007BFF; border-radius: 5px; margin: 5px 0px 15px 0px; }
div.stButton > button:first-child { width: 100%; }
.res-card { padding: 12px; border-radius: 10px; margin-bottom: 8px; border-left: 5px solid #ccc; font-size: 14px; }
.card-nuevo { background-color: #e8f5e9; border-left-color: #2e7d32; } /* Verde */
.card-rotado { background-color: #fffde7; border-left-color: #fbc02d; } /* Amarillo */
.card-mantiene { background-color: #e3f2fd; border-left-color: #1976d2; } /* Azul */
.leyenda-box { background-color: #ffffff; padding: 15px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 20px; }
.baja-card { background-color: #fff5f5; padding: 10px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 5px; }
.header-info { background-color: #e9ecef; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #ccc; }
</style>
""", unsafe_allow_html=True)

st.title("Taller de Electrónica - Gestión de Neumáticos")

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

def borrar_todo():
    st.session_state.reset_key += 1
    st.rerun()

# --- Identificación del Vehículo ---
st.markdown("### 📋 Identificación del Vehículo")
st.markdown('<div class="blue-line"></div>', unsafe_allow_html=True)

col_id1, col_id2 = st.columns(2)
with col_id1:
    num_bus = st.text_input("Número de Bus:", placeholder="Ej: 1024", key=f"bus_{st.session_state.reset_key}")
with col_id2:
    ppu_bus = st.text_input("PPU (Patente):", placeholder="Ej: ABCD-12", key=f"ppu_{st.session_state.reset_key}")

tipo_bus = st.radio("Tipo de bus:", ('Rígido (6 ruedas)', 'Articulado (10 ruedas)'), key=f"tipo_{st.session_state.reset_key}")
total_pos = 10 if tipo_bus == 'Articulado (10 ruedas)' else 6

prof_ini = []
est_ini = []

def renderizar_eje(titulo, indices):
    st.markdown(f"### {titulo}")
    st.markdown('<div class="blue-line"></div>', unsafe_allow_html=True)
    cols = st.columns(len(indices))
    for idx, p_idx in enumerate(indices):
        with cols[idx]:
            st.write(f"**Pos {p_idx + 1}**")
            val = st.number_input(f"mm", min_value=0.0, max_value=25.0, value=None, key=f"p{p_idx}_{st.session_state.reset_key}")
            est = st.radio(f"Estado", options=["OK", "DAÑO"], horizontal=True, key=f"e{p_idx}_{st.session_state.reset_key}")
            prof_ini.append(val if val is not None else 0.0)
            est_ini.append('o' if est == "OK" else 'd')

renderizar_eje("EJE 1 (DIRECCIONAL)", [0, 1])
renderizar_eje("EJE 2 (TRACCIÓN)", [2, 3, 4, 5])
if total_pos == 10:
    renderizar_eje("EJE 3 (ARTICULADO)", [6, 7, 8, 9])

st.write("")
col_run, col_del = st.columns(2)
with col_del: st.button("🗑️ Borrar Datos", on_click=borrar_todo)
with col_run: ejecutar = st.button("🚀 Generar Plan", type="primary")

if ejecutar:
    # Parámetros y reglas (Instrucción K < G o N < G -> No)
    G_LIMITE = 4.0   
    MAX_DIF = 4.0    
    VALOR_E1 = 18.0  
    VALOR_E_TRA = 16.0 
    LIMITE_ROTAR_MAX = 12.0
    LIMITE_ROTAR_MIN = 5.0

    finales = prof_ini.copy()
    origen_neumatico = ["mantiene"] * total_pos 
    stock_donante = [] 
    lista_bajas = []
    bitacora_detallada = []

    ejes_indices = [[2,3,4,5]]
    if total_pos == 10: ejes_indices.append([6,7,8,9])
    
    # Análisis previo de tracción
    conteo_bajas_traseras = 0
    necesita_intervencion_trasera = False
    for eje in ejes_indices:
        bajas_en_este_eje = [p for p in eje if est_ini[p] == 'd' or prof_ini[p] <= G_LIMITE]
        conteo_bajas_traseras += len(bajas_en_este_eje)
        vivos = [prof_ini[p] for p in eje if est_ini[p] == 'o' and prof_ini[p] > G_LIMITE]
        if len(bajas_en_este_eje) > 0 or (len(vivos) > 0 and (max(vivos) - min(vivos) > MAX_DIF)):
            necesita_intervencion_trasera = True

    # --- LÓGICA EJE 1 ---
    e1_apto_rango = all(LIMITE_ROTAR_MIN <= prof_ini[p] <= LIMITE_ROTAR_MAX and est_ini[p] == 'o' for p in [0,1])
    e1_caro = all(prof_ini[p] > LIMITE_ROTAR_MAX and est_ini[p] == 'o' for p in [0,1])
    
    rotar_por_rango = necesita_intervencion_trasera and e1_apto_rango
    rotar_por_emergencia = necesita_intervencion_trasera and e1_caro and conteo_bajas_traseras >= 3

    if rotar_por_rango or rotar_por_emergencia:
        for p in [0, 1]:
            stock_donante.append({'pos': p+1, 'mm': prof_ini[p]})
            finales[p] = VALOR_E1
            origen_neumatico[p] = "nuevo"
        motivo = "Rango eficiente (5-12mm)" if rotar_por_rango else f"Emergencia por {conteo_bajas_traseras} bajas traseras"
        bitacora_detallada.append(f"✅ **Eje 1 Renovado:** Se rotaron neumáticos a tracción por {motivo}.")
    else:
        for p in [0, 1]:
            if prof_ini[p] <= G_LIMITE or est_ini[p] == 'd':
                lista_bajas.append({'pos': p+1, 'mm': prof_ini[p]})
                finales[p] = VALOR_E1
                origen_neumatico[p] = "nuevo"
                bitacora_detallada.append(f"⚠️ **Eje 1 - Pos {p+1}:** Cambio obligatorio por desgaste/daño.")
            else:
                bitacora_detallada.append(f"ℹ️ **Eje 1 - Pos {p+1}:** Se mantiene. Eficiencia económica: medida > 12mm.")

    # --- LÓGICA EJES TRASEROS ---
    for eje in ejes_indices:
        for p in eje:
            if prof_ini[p] <= G_LIMITE or est_ini[p] == 'd':
                lista_bajas.append({'pos': p+1, 'mm': prof_ini[p]})
                finales[p] = None
        
        while True:
            vivos = [finales[p] for p in eje if finales[p] is not None]
            obj = max(vivos) if vivos else VALOR_E_TRA
            cambio = False
            for p in eje:
                if finales[p] is None or (obj - finales[p] > MAX_DIF):
                    if finales[p] is not None: stock_donante.append({'pos': p+1, 'mm': finales[p]})
                    stock_donante.sort(key=lambda x: abs(x['mm'] - obj))
                    
                    if stock_donante and abs(stock_donante[0]['mm'] - obj) <= MAX_DIF:
                        item = stock_donante.pop(0)
                        finales[p] = item['mm']
                        origen_neumatico[p] = "rotado"
                        bitacora_detallada.append(f"🔄 **Pos {p+1}:** Homologado con neumático rotado de {item['mm']}mm.")
                    else:
                        finales[p] = VALOR_E_TRA
                        origen_neumatico[p] = "nuevo"
                        bitacora_detallada.append(f"🆕 **Pos {p+1}:** Instalado Recauchado Nuevo (16mm).")
                    cambio = True
                if cambio: break
            if not cambio: break

    # --- REPORTE FINAL ---
    st.markdown("---")
    st.markdown(f"""<div class="header-info"><h2 style='margin:0;'>✅ REPORTE TÉCNICO FINAL</h2><strong>Bus:</strong> {num_bus if num_bus else 'S/N'} | <strong>PPU:</strong> {ppu_bus if ppu_bus else 'S/P'}</div>""", unsafe_allow_html=True)
    
    # 1. Análisis Detallado
    with st.expander("🔍 VER ANÁLISIS ESTRATÉGICO DETALLADO", expanded=True):
        for msg in bitacora_detallada:
            st.write(msg)

    # 2. Leyenda Fija
    st.markdown("### 🗺️ Guía de Colores (Leyenda)")
    st.markdown("""
    <div class="leyenda-box">
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; background-color: #fbc02d; margin-right: 10px; border-radius: 3px;"></div>
            <span><b>Amarillo (Rotado):</b> Neumáticos que vienen del Eje 1 hacia tracción.</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; background-color: #2e7d32; margin-right: 10px; border-radius: 3px;"></div>
            <span><b>Verde (Nuevo):</b> Nuevos 18mm (Eje 1) o Recauchados 16mm (Tracción).</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: #1976d2; margin-right: 10px; border-radius: 3px;"></div>
            <span><b>Azul (Mantiene):</b> Neumáticos que NO se movieron de su lugar.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Plan de Acción
    st.success("### 🛠️ Configuración Final del Bus")
    for i in range(total_pos):
        clase = "card-nuevo" if origen_neumatico[i] == "nuevo" else "card-rotado" if origen_neumatico[i] == "rotado" else "card-mantiene"
        st.markdown(f"""
        <div class="res-card {clase}">
            <strong>POSICIÓN {i+1}</strong><br>
            Estado: {prof_ini[i]}mm &rarr; <b>{finales[i]:.1f}mm</b> | Origen: <i>{origen_neumatico[i].upper()}</i>
        </div>
        """, unsafe_allow_html=True)

    # 4. Bajas
    if lista_bajas:
        st.error("### ❌ Neumáticos para Retiro")
        for b in lista_bajas:
            st.write(f"• Posición {b['pos']} ({b['mm']}mm) - Fuera de servicio.")
