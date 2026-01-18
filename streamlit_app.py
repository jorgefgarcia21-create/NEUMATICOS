import streamlit as st

# Configuración de página
st.set_page_config(page_title="Gestión de Neumáticos", page_icon="🛞", layout="centered")

# Estilos CSS (Sin tabulaciones para evitar errores de depuración)
st.markdown("""
<style>
.blue-line { border-top: 3px solid #007BFF; border-radius: 5px; margin: 5px 0px 15px 0px; }
div.stButton > button:first-child { width: 100%; }
.res-card { background-color: #f8f9fa; padding: 12px; border-radius: 10px; margin-bottom: 8px; border-left: 5px solid #007BFF; }
.baja-card { background-color: #fff5f5; padding: 10px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 5px; }
.stock-card { background-color: #f0f7ff; padding: 10px; border-radius: 8px; border-left: 5px solid #007BFF; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("Taller de Electrónica - Gestión de Neumáticos")

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

def borrar_todo():
    st.session_state.reset_key += 1
    st.rerun()

# --- Interfaz de Usuario ---
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
    # Lógica de Negocio (K < G o N < G -> No/Baja)
    G_LIMITE = 4.0   
    MAX_DIF = 4.0    
    VALOR_E1 = 18.0  
    VALOR_E_TRA = 16.0 

    finales = prof_ini.copy()
    stock_donante = [] 
    lista_bajas = []
    bitacora = []

    ejes_indices = [[2,3,4,5]]
    if total_pos == 10: ejes_indices.append([6,7,8,9])
    
    necesita_intervencion_trasera = False
    for eje in ejes_indices:
        vivos = [prof_ini[p] for p in eje if est_ini[p] == 'o' and prof_ini[p] > G_LIMITE]
        if len(vivos) < len(eje) or (len(vivos) > 0 and (max(vivos) - min(vivos) > MAX_DIF)):
            necesita_intervencion_trasera = True

    # Fase Eje 1
    e1_apto_donar = all(est_ini[p] == 'o' and prof_ini[p] > G_LIMITE for p in [0,1])
    if necesita_intervencion_trasera and e1_apto_donar:
        for p in [0, 1]:
            stock_donante.append({'pos': p+1, 'mm': prof_ini[p]})
            finales[p] = VALOR_E1
        bitacora.append("Eje 1: Renovado completo para donar neumáticos a tracción.")
    elif any(prof_ini[p] <= G_LIMITE or est_ini[p] == 'd' for p in [0,1]):
        for p in [0, 1]:
            if est_ini[p] == 'o' and prof_ini[p] > G_LIMITE:
                stock_donante.append({'pos': p+1, 'mm': prof_ini[p]})
            else:
                lista_bajas.append({'pos': p+1, 'mm': prof_ini[p]})
            finales[p] = VALOR_E1
        bitacora.append("Eje 1: Renovado por desgaste o daños detectados.")

    # Fase Ejes Traseros
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
                        bitacora.append(f"Pos {p+1}: Nivelado con neumático de {item['mm']}mm.")
                        cambio = True
                    else:
                        finales[p] = VALOR_E_TRA
                        bitacora.append(f"Pos {p+1}: Instalado Recauchado Nuevo (16mm).")
                        cambio = True
                if cambio: break
            if not cambio: break

    # --- SALIDA DE DATOS ORDENADA ---
    st.markdown("---")
    
    # 1. ANÁLISIS ESTRATÉGICO
    st.info("### 1. Análisis del Sistema")
    for msg in bitacora:
        st.write(f"• {msg}")

    # 2. PLAN DE ACCIÓN (ORDEN 1-10)
    st.success("### 2. Plan de Acción por Posición")
    for i in range(total_pos):
        es_cambio = finales[i] != prof_ini[i]
        color = "#e3f2fd" if es_cambio else "#f1f8e9"
        st.markdown(f"""
        <div class="res-card" style="background-color: {color};">
            <strong>POSICIÓN {i+1}</strong><br>
            Actual: {prof_ini[i]}mm | Final: <strong>{finales[i]:.1f}mm</strong>
        </div>
        """, unsafe_allow_html=True)

    # 3. BAJAS DETECTADAS (ORDENADAS)
    if lista_bajas:
        st.error("### 3. Neumáticos de Baja (Retiro)")
        lista_bajas.sort(key=lambda x: x['pos'])
        for b in lista_bajas:
            st.markdown(f"""<div class="baja-card">Posición {b['pos']}: {b['mm']}mm (Desgaste/Daño)</div>""", unsafe_allow_html=True)

    # 4. STOCK DISPONIBLE (ORDENADO)
    if stock_donante:
        st.warning("### 4. Stock Sobrante (Para Almacén)")
        stock_donante.sort(key=lambda x: x['pos'])
        for s in stock_donante:
            st.markdown(f"""<div class="stock-card">De Posición {s['pos']}: {s['mm']}mm disponible</div>""", unsafe_allow_html=True)
