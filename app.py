import streamlit as st
import math
import pandas as pd  # Necesar pentru tabele și Excel
import io          # <-- NOU: Necesar pentru a crea fișierul în memorie

# ======================================================================
# PARTEA 1: DATELE DIN NORMATIVUL I9-2022 (Neschimbată)
# ======================================================================

# [cite_start]Date conform ANEXA 2.1A (Clădiri de locuit) [cite: 2383-2387]
DATE_LOCUIT = {
    'lavoar_sec': {'nume': 'Lavoar (grup sanitar secundar)', 'ui': 1, 'vs': 0.10},
    'lavoar_princ': {'nume': 'Lavoar (grup sanitar principal)', 'ui': 1.5, 'vs': 0.15},
    'bideu': {'nume': 'Bideu', 'ui': 1, 'vs': 0.10},
    'dus': {'nume': 'Duș', 'ui': 2, 'vs': 0.20},
    'spalator_1_2': {'nume': 'Spălător (baterie 1/2")', 'ui': 2, 'vs': 0.20},
    'spalator_3_4': {'nume': 'Spălător (baterie 3/4")', 'ui': 3, 'vs': 0.33},
    'cada_mica': {'nume': 'Cadă baie (< 150 l)', 'ui': 3, 'vs': 0.25},
    'cada_mare': {'nume': 'Cadă baie (> 150 l)', 'ui': 4, 'vs': 0.33},
    'vc_rezervor': {'nume': 'VC (cu rezervor spălare)', 'ui': 1, 'vs': 0.12},
    'vc_presiune': {'nume': '🚽 VC (cu robinet spălare sub presiune)', 'ui': 15, 'vs': 1.5},
    'msv': {'nume': 'Mașină spălat vase', 'ui': 2, 'vs': 0.20},
    'msr': {'nume': 'Mașină spălat rufe', 'ui': 2, 'vs': 0.20}
}

# [cite_start]Date conform ANEXA 2.1B (Alte clădiri) [cite: 2392-2397]
DATE_ALTE_CLADIRI = {
    'lavoar_comun': {'nume': 'Lavoar (grupuri sanitare comune)', 'e1': 0.5, 'e2': 0, 'vs': 0.10},
    'dus': {'nume': 'Duș', 'e1': 1, 'e2': 0, 'vs': 0.20},
    'spalator_1_2': {'nume': 'Spălător (baterie 1/2")', 'e1': 1, 'e2': 0, 'vs': 0.20},
    'chiuveta': {'nume': 'Chiuvetă', 'e1': 0, 'e2': 1, 'vs': 0.2},
    'vc_rezervor': {'nume': 'VC (cu rezervor spălare)', 'e1': 0, 'e2': 0.6, 'vs': 0.12},
    'vc_presiune': {'nume': '🚽 VC (cu robinet spălare sub presiune)', 'e1': 0, 'e2': 7.5, 'vs': 1.5},
    'pisoar_robinet': {'nume': 'Pisoar (robinet individual)', 'e1': 0, 'e2': 0.75, 'vs': 0.15},
    'pisoar_vacuum': {'nume': 'Pisoar (spălare vacuumatică)', 'e1': 0, 'e2': 2.50, 'vs': 0.50},
    'msv': {'nume': 'Mașină spălat vase', 'e1': 0, 'e2': 1, 'vs': 0.2},
    'msr': {'nume': 'Mașină spălat rufe', 'e1': 0, 'e2': 1, 'vs': 0.2}
}

# [cite_start]Date conform Tabel 11.1 (Formule Metoda C) [cite: 803-806]
FORMULE_METODA_C = {
    'camine_copii': {'nume': 'Cămine pentru copii, creșe', 'factor_e': 0.20, 'min_e': 1.0},
    'teatre': {'nume': 'Teatre, cluburi, cinematografe, gări', 'factor_e': 0.22, 'min_e': 1.2},
    'birouri': {'nume': 'Birouri, magazine, grupuri sanitare hale', 'factor_e': 0.24, 'min_e': 1.4},
    'scoli': {'nume': 'Instituții de învăţământ', 'factor_e': 0.27, 'min_e': 1.8},
    'spitale': {'nume': 'Spitale, sanatorii, cantine', 'factor_e': 0.30, 'min_e': 2.2},
    'hoteluri_comune': {'nume': 'Hoteluri (grupuri sanitare comune)', 'factor_e': 0.38, 'min_e': 3.6},
    'camine_studenti': {'nume': 'Cămine de studenți, băi publice', 'factor_e': 0.45, 'min_e': 5.0},
    'vestiare_productie': {'nume': 'Grupuri sanitare vestiare producție', 'factor_e': 0.90, 'min_e': 20.0}
}

# [cite_start]SIMULARE NOMOGRAMA [cite: 2989-3057]
NOMOGRAMA_PPR = [
    # Vc_max, De-g,   v,   i (Pa/m)
    [0.20, "20-1.7", 0.9, 600],
    [0.39, "25-1.9", 1.0, 650],
    [0.55, "32-2.2", 0.9, 475],
    [1.10, "40-2.4", 1.1, 420],
    [2.00, "50-2.9", 1.2, 375],
    [3.50, "63-3.6", 1.4, 350],
    [6.00, "75-4.3", 1.7, 400],
    [9.50, "90-5.1", 1.9, 450]
]

# ======================================================================
# PARTEA 2: FUNCȚII HELPER
# ======================================================================

def get_dimensiune_teava(Vc):
    """ Simulează căutarea pe nomogramă. """
    for teava in NOMOGRAMA_PPR:
        if Vc <= teava[0]:
            return {
                'De_g': teava[1],
                'v': teava[2],
                'i': teava[3]
            }
    return {'De_g': "PREA MARE (>DN90)", 'v': -1, 'i': -1}

def add_fixture():
    """ Adaugă un rând nou pentru un obiect sanitar în session_state. """
    new_id = st.session_state.next_id
    default_key_list = list(DATE_LOCUIT.keys()) if st.session_state.building_type_selector == 'locuit' else list(DATE_ALTE_CLADIRI.keys())
    st.session_state.fixtures[new_id] = {'key': default_key_list[0], 'count': 1}
    st.session_state.next_id += 1

def delete_fixture(id_to_delete):
    """ Șterge un rând de obiect sanitar din session_state. """
    if id_to_delete in st.session_state.fixtures:
        del st.session_state.fixtures[id_to_delete]
    if not st.session_state.fixtures:
        add_fixture()
    st.rerun()

def update_tronson_name():
    """ Sincronizează starea aplicației cu ce scrie utilizatorul în căsuță. """
    st.session_state.tronson_name = st.session_state.tronson_name_input

# --- NOU: Funcție pentru a converti DataFrame în Excel ---
def to_excel(df):
    """
    Converteste un DataFrame pandas intr-un fisier Excel in memorie.
    """
    output_buffer = io.BytesIO()
    # Folosim engine='xlsxwriter' pentru a putea formata coloanele
    with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Tronson_Calcul')
        
        # (Bonus) Ajustare automată a lățimii coloanelor
        workbook = writer.book
        worksheet = writer.sheets['Tronson_Calcul']
        for i, col in enumerate(df.columns):
            # Găsește lățimea maximă a coloanei
            column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)
            
    # Preluăm datele binare ale fișierului creat
    excel_data = output_buffer.getvalue()
    return excel_data

# ======================================================================
# PARTEA 3: INTERFAȚA STREAMLIT
# ======================================================================

def run_app():
    st.set_page_config(page_title="Calculator I9", layout="centered")
    st.title("🚰 Calculator Dimensionare I9-2022")
    st.write("Realizat de **Gem de Sanitare** pe baza Normativului I9-2022.")

    # --- Inițializare Session State ---
    if 'fixtures' not in st.session_state:
        st.session_state.fixtures = {0: {'key': 'lavoar_princ', 'count': 1}}
    if 'next_id' not in st.session_state:
        st.session_state.next_id = 1
    if 'saved_tronsons' not in st.session_state:
        st.session_state.saved_tronsons = []
    if 'tronson_name' not in st.session_state:
        st.session_state.tronson_name = "Tronson 1"
    if 'building_type_selector' not in st.session_state:
        st.session_state.building_type_selector = 'locuit'

    # --- INPUTURI (în Sidebar) ---
    st.sidebar.header("1. Selectare Tronson")
    building_type_key = st.sidebar.selectbox(
        "Tip Clădire:",
        options=['locuit', 'alte'],
        format_func=lambda x: "Clădire de locuit (Metoda B)" if x == 'locuit' else "Alte clădiri (Metoda C)",
        key="building_type_selector"
    )

    # Resetăm rândurile de obiecte dacă se schimbă tipul clădirii
    if 'last_building_type' not in st.session_state:
        st.session_state.last_building_type = building_type_key

    if st.session_state.last_building_type != building_type_key:
        st.session_state.last_building_type = building_type_key
        default_key_list = list(DATE_LOCUIT.keys()) if building_type_key == 'locuit' else list(DATE_ALTE_CLADIRI.keys())
        st.session_state.fixtures = {0: {'key': default_key_list[0], 'count': 1}}
        st.session_state.next_id = 1
        st.rerun()

    if building_type_key == 'locuit':
        active_data = DATE_LOCUIT
        unit_label = "Ui"
    else:
        active_data = DATE_ALTE_CLADIRI
        unit_label = "E"

    subtype_key = None
    if building_type_key == 'alte':
        subtype_key = st.sidebar.selectbox(
            "Subtip Clădire (Tabel 11.1):",
            options=list(FORMULE_METODA_C.keys()),
            format_func=lambda x: FORMULE_METODA_C[x]['nume']
        )
    st.sidebar.divider()
    
    # --- Formularul Dinamic pentru Obiecte Sanitare ---
    st.header("2. Obiecte Sanitare deservite")
    
    fixture_keys = list(active_data.keys())
    fixture_names = [active_data[key]['nume'] for key in fixture_keys]

    for fixture_id, fixture_data in list(st.session_state.fixtures.items()):
        current_key = fixture_data['key']
        if current_key not in active_data:
            current_key = fixture_keys[0]
            st.session_state.fixtures[fixture_id]['key'] = current_key

        current_index = fixture_keys.index(current_key)
        col1, col2, col3 = st.columns([4, 1, 1])
        
        selected_name = col1.selectbox(
            "Obiect Sanitar", options=fixture_names, index=current_index,
            key=f"select_{fixture_id}", label_visibility="collapsed"
        )
        st.session_state.fixtures[fixture_id]['key'] = fixture_keys[fixture_names.index(selected_name)]
        
        new_count = col2.number_input(
            "Cant.", min_value=1, value=fixture_data['count'],
            key=f"count_{fixture_id}", label_visibility="collapsed"
        )
        st.session_state.fixtures[fixture_id]['count'] = new_count
        
        col3.button("❌", key=f"del_{fixture_id}", on_click=delete_fixture, args=(fixture_id,))

    st.button("➕ Adaugă Obiect Sanitar", on_click=add_fixture)
    st.divider()

    # --- Câmp pentru numele tronsonului (Corectat) ---
    st.text_input(
        "Numele Tronsonului de calculat:",
        value=st.session_state.tronson_name,
        key="tronson_name_input",
        on_change=update_tronson_name
    )
    
    # --- Butonul de Calcul și Afișarea Rezultatelor ---
    if st.button("Calculează și Salvează Tronsonul", type="primary", use_container_width=True):
        
        calcul_summary = {}
        N_total = 0
        U_total = 0
        E_total = 0
        Vs_total = 0
        Vc = 0.0
        inputs_list_str = []

        # 1. Însumare totaluri
        for fixture_data in st.session_state.fixtures.values():
            key = fixture_data['key']
            count = fixture_data['count']
            if not key or count <= 0: continue
            
            nume_obiect = active_data.get(key, {}).get('nume', 'Necunoscut')
            inputs_list_str.append(f"{count}x {nume_obiect}")
            N_total += count
            
            if building_type_key == 'locuit':
                data = DATE_LOCUIT[key]
                U_total += data['ui'] * count
                Vs_total += data['vs'] * count
            else:
                data = DATE_ALTE_CLADIRI[key]
                E_total += (data['e1'] + data['e2']) * count
        
        st.header("3. Rezultate Calcul")
        
        # 2. Aplicare logică de calcul I9
        if building_type_key == 'locuit':
            calcul_summary["Metodă"] = "Metoda B (Locuit)"
            calcul_summary["Total Unit. Consum (U)"] = f"{U_total:.2f}"
            calcul_summary["Total Obiecte (N)"] = N_total
            calcul_summary["Total Debit Specific (Vs_tot)"] = f"{Vs_total:.2f} l/s"

            f_AR = 1.0
            if N_total > 1: f_AR = 0.83 / math.sqrt(N_total - 1)
            calcul_summary["Factor Simultan. (f_AR)"] = f"{f_AR:.4f}"

            if U_total < 15:
                Dmin_metodaA = -0.035 * (U_total**2) + 1.4 * U_total + 10.9
                st.info(f"**Verificare Metoda A (pentru U < 15):**\nDiametrul Minim Interior (Dmin) = **{Dmin_metodaA:.2f} mm**")
                Vc = Vs_total if N_total == 1 else (Vs_total * f_AR) + 0.03
                calcul_summary["Calcul Vc (B.1)"] = f"({Vs_total:.2f} * {f_AR:.4f}) + 0.03"
            else:
                Vc = Vs_total * f_AR
                calcul_summary["Calcul Vc (B.2)"] = f"{Vs_total:.2f} * {f_AR:.4f}"

        else:
            formula_data = FORMULE_METODA_C[subtype_key]
            calcul_summary["Metodă"] = f"Metoda C ({formula_data['nume']})"
            calcul_summary["Total Echivalenți (E)"] = f"{E_total:.2f}"
            
            if E_total < formula_data['min_e']:
                Vc = 0.2 * E_total
                calcul_summary["Calcul Vc"] = f"(E < {formula_data['min_e']}, Vc = 0.2 * E)"
            else:
                Vc = formula_data['factor_e'] * math.sqrt(E_total)
                calcul_summary["Calcul Vc"] = f"({formula_data['factor_e']} * sqrt({E_total:.2f}))"
        
        calcul_summary["Debit de Calcul (Vc)"] = f"{Vc:.3f} l/s"

        # 3. Găsire Dimensiune (Simulare Nomogramă)
        teava = get_dimensiune_teava(Vc)
        
        # 4. AFIȘARE REZULTATE CURENTE
        st.subheader("Sumar Calcul Tronson Curent:")
        st.json(calcul_summary)
        
        if teava['v'] != -1:
            st.success(
                f"**Debit de Calcul (Vc): {Vc:.3f} l/s**\n\n"
                f"**Dimensiune Recomandată (PPR):**\n"
                f"- **Diametru (De-g): {teava['De_g']} mm**\n"
                f"- **Viteză (v): {teava['v']:.2f} m/s**\n"
                f"- **Pierdere Liniară (i): {teava['i']:.0f} Pa/m**"
            )

            # 5. Salvarea datelor tronsonului
            tronson_data = {
                'Nume Tronson': st.session_state.tronson_name_input,
                'Metodă': calcul_summary.get("Metodă", ""),
                'Obiecte': ", ".join(inputs_list_str),
                'N (buc)': N_total,
                f"{unit_label} Total": f"{U_total:.2f}" if building_type_key == 'locuit' else f"{E_total:.2f}",
                'Vc (l/s)': f"{Vc:.3f}",
                'De-g (mm)': teava['De_g'],
                'v (m/s)': f"{teava['v']:.2f}",
                'i (Pa/m)': f"{teava['i']:.0f}"
            }
            st.session_state.saved_tronsons.append(tronson_data)

            # 6. Incrementarea automată a numelui tronsonului
            try:
                current_name = st.session_state.tronson_name_input
                parts = current_name.split(' ')
                num = int(parts[-1])
                base_name = " ".join(parts[:-1])
                st.session_state.tronson_name = f"{base_name} {num + 1}"
            except:
                st.session_state.tronson_name = f"{current_name} 2"
        
        else:
            st.error("Debitul de calcul este prea mare pentru nomograma predefinită (>DN90).")
        
        st.rerun()

    # --- SECȚIUNEA PENTRU AFISAREA TRONSOANELOR SALVATE ---
    st.divider()
    st.header("4. Tronsoane Salvate în Sesiune")

    if not st.session_state.saved_tronsons:
        st.info("Niciun tronson salvat. Calculează un tronson pentru a-l adăuga în listă.")
    else:
        df = pd.DataFrame(st.session_state.saved_tronsons)
        st.dataframe(df, use_container_width=True)
        
        # --- NOU: Butonul de descărcare Excel ---
        # 1. Creăm fișierul Excel în memorie
        excel_data = to_excel(df)
        
        # 2. Oferim fișierul la descărcat
        st.download_button(
            label="📥 Descarcă Lista Tronsoanelor (.xlsx)",
            data=excel_data,
            file_name="dimensionare_tronsoane.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        # --- Butonul de ștergere (existent) ---
        if st.button("Șterge Toate Tronsoanele", type="secondary"):
            st.session_state.saved_tronsons = []
            st.session_state.tronson_name = "Tronson 1"
            st.rerun()

# Punctul de intrare al aplicației
if __name__ == "__main__":
    run_app()