import streamlit as st
import math
import pandas as pd  # <-- Am adăugat importul PANDAS pentru tabele frumoase

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

# [cite_start]SIMULARE NOMOGRAMA (Neschimbată) [cite: 2989-3057]
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
# PARTEA 2: FUNCȚII HELPER (Neschimbate)
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
    st.session_state.fixtures[new_id] = {'key': list(DATE_LOCUIT.keys())[0], 'count': 1}
    st.session_state.next_id += 1

def delete_fixture(id_to_delete):
    """ Șterge un rând de obiect sanitar din session_state. """
    if id_to_delete in st.session_state.fixtures:
        del st.session_state.fixtures[id_to_delete]
        
    # Dacă nu mai există niciun rând, adaugă unul gol
    if not st.session_state.fixtures:
        add_fixture()
        
    st.rerun() # Forțează redesenarea

# ======================================================================
# PARTEA 3: INTERFAȚA STREAMLIT (Cu modificări)
# ======================================================================

def run_app():
    st.set_page_config(page_title="Calculator I9", layout="centered")
    st.title("🚰 Calculator Dimensionare I9-2022")
    st.write("Realizat de **Gem de Sanitare** pe baza Normativului I9-2022.")

    # --- Inițializare Session State (Am adăugat 'saved_tronsons' și 'tronson_name') ---
    if 'fixtures' not in st.session_state:
        st.session_state.fixtures = {0: {'key': 'lavoar_princ', 'count': 1}}
    if 'next_id' not in st.session_state:
        st.session_state.next_id = 1
    if 'saved_tronsons' not in st.session_state:
        st.session_state.saved_tronsons = [] # <-- NOU: Lista pentru tronsoane salvate
    if 'tronson_name' not in st.session_state:
        st.session_state.tronson_name = "Tronson 1" # <-- NOU: Numele tronsonului curent

    # --- INPUTURI (în Sidebar) ---
    st.sidebar.header("1. Selectare Tronson")
    building_type_key = st.sidebar.selectbox(
        "Tip Clădire:",
        options=['locuit', 'alte'],
        format_func=lambda x: "Clădire de locuit (Metoda B)" if x == 'locuit' else "Alte clădiri (Metoda C)",
        key="building_type_selector" # Adăugăm o cheie
    )

    # Resetăm rândurile de obiecte dacă se schimbă tipul clădirii
    # Verificăm dacă tipul selectat e diferit de cel salvat (dacă există unul salvat)
    if 'last_building_type' not in st.session_state:
        st.session_state.last_building_type = building_type_key

    if st.session_state.last_building_type != building_type_key:
        st.session_state.last_building_type = building_type_key
        st.session_state.fixtures = {0: {'key': list(DATE_LOCUIT.keys())[0], 'count': 1}}
        st.session_state.next_id = 1
        st.rerun()

    # Alege setul de date și unitatea de măsură corectă
    if building_type_key == 'locuit':
        active_data = DATE_LOCUIT
        unit_label = "Ui"
    else:
        active_data = DATE_ALTE_CLADIRI
        unit_label = "E"

    # Afișează subtipul de clădire DOAR dacă e Metoda C
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

    # Parcurgem dictionarul de obiecte din session_state
    for fixture_id, fixture_data in list(st.session_state.fixtures.items()): # Folosim list() pentru a permite ștergerea
        
        current_key = fixture_data['key']
        # Verificăm dacă cheia există în setul de date activ
        if current_key not in active_data:
            current_key = fixture_keys[0] # Resetăm la prima opțiune
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

    # --- NOU: Câmp pentru numele tronsonului ---
    st.text_input("Numele Tronsonului de calculat:", key="tronson_name")
    
    # --- Butonul de Calcul și Afișarea Rezultatelor ---
    if st.button("Calculează și Salvează Tronsonul", type="primary", use_container_width=True):
        
        calcul_summary = {}
        N_total = 0
        U_total = 0
        E_total = 0
        Vs_total = 0
        Vc = 0.0
        inputs_list_str = [] # Listă pentru a stoca obiectele adăugate

        # 1. Însumare totaluri
        for fixture_data in st.session_state.fixtures.values():
            key = fixture_data['key']
            count = fixture_data['count']
            
            if not key or count <= 0: continue
            
            # Adăugăm la lista de inputuri pentru salvare
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
            # --- METODA A & B (Locuit) ---
            calcul_summary["Metodă"] = "Metoda B (Locuit)"
            calcul_summary["Total Unit. Consum (U)"] = f"{U_total:.2f}"
            calcul_summary["Total Obiecte (N)"] = N_total
            calcul_summary["Total Debit Specific (Vs_tot)"] = f"{Vs_total:.2f} l/s"

            f_AR = 1.0
            if N_total > 1:
                f_AR = 0.83 / math.sqrt(N_total - 1)
            calcul_summary["Factor Simultan. (f_AR)"] = f"{f_AR:.4f}"

            if U_total < 15:
                # [cite_start]Verificare Metoda A [cite: 723]
                Dmin_metodaA = -0.035 * (U_total**2) + 1.4 * U_total + 10.9
                st.info(f"**Verificare Metoda A (pentru U < 15):**\nDiametrul Minim Interior (Dmin) = **{Dmin_metodaA:.2f} mm**")

                # [cite_start]Calcul Metoda B.1 [cite: 777-781]
                if N_total == 1:
                    Vc = Vs_total
                else:
                    Vc = (Vs_total * f_AR) + 0.03
                calcul_summary["Calcul Vc (B.1)"] = f"({Vs_total:.2f} * {f_AR:.4f}) + 0.03"
            
            else:
                # [cite_start]Calcul Metoda B.2 [cite: 789-791]
                Vc = Vs_total * f_AR
                calcul_summary["Calcul Vc (B.2)"] = f"{Vs_total:.2f} * {f_AR:.4f}"

        else:
            # --- METODA C (Alte Clădiri) ---
            formula_data = FORMULE_METODA_C[subtype_key]
            calcul_summary["Metodă"] = f"Metoda C ({formula_data['nume']})"
            calcul_summary["Total Echivalenți (E)"] = f"{E_total:.2f}"
            
            if E_total < formula_data['min_e']:
                # [cite_start]Sub pragul minim [cite: 807-808]
                Vc = 0.2 * E_total
                calcul_summary["Calcul Vc"] = f"(E < {formula_data['min_e']}, Vc = 0.2 * E)"
            else:
                # [cite_start]Peste prag [cite: 803-806]
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

            # 5. NOU: Salvarea datelor tronsonului
            tronson_data = {
                'Nume Tronson': st.session_state.tronson_name,
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

            # NOU: Incrementarea automată a numelui tronsonului
            try:
                # Încearcă să găsească un număr la finalul numelui
                parts = st.session_state.tronson_name.split(' ')
                num = int(parts[-1])
                base_name = " ".join(parts[:-1])
                st.session_state.tronson_name = f"{base_name} {num + 1}"
            except:
                # Dacă eșuează (ex: numele era "Coloana"), adaugă "2"
                st.session_state.tronson_name = f"{st.session_state.tronson_name} 2"
        
        else:
            st.error("Debitul de calcul este prea mare pentru nomograma predefinită (>DN90).")

    # --- NOU: SECȚIUNEA PENTRU AFISAREA TRONSOANELOR SALVATE ---
    st.divider()
    st.header("4. Tronsoane Salvate în Sesiune")

    if not st.session_state.saved_tronsons:
        st.info("Niciun tronson salvat. Calculează un tronson pentru a-l adăuga în listă.")
    else:
        # Folosim Pandas DataFrame pentru un tabel frumos
        df = pd.DataFrame(st.session_state.saved_tronsons)
        st.dataframe(df, use_container_width=True)
        
        # Buton pentru a șterge lista
        if st.button("Șterge Toate Tronsoanele", type="secondary"):
            st.session_state.saved_tronsons = []
            st.session_state.tronson_name = "Tronson 1" # Resetăm și numele
            st.rerun()

# Punctul de intrare al aplicației
if __name__ == "__main__":
    run_app()