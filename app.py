import streamlit as st
import math

# ======================================================================
# PARTEA 1: DATELE DIN NORMATIVUL I9-2022
# ======================================================================

# Date conform ANEXA 2.1A (Clădiri de locuit) [cite: 2383-2387]
# Folosim Unități de Consum (Ui) și Debite Specifice (Vs)
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
# Date conform ANEXA 2.1B (Alte clădiri) 
# Folosim Echivalenți de Debit (E)
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
# Date conform Tabel 11.1 (Formule Metoda C) 
# (factor_e = 0.24 in Vc = 0.24 * E^0.5)
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

# SIMULARE NOMOGRAMA (bazat pe CSV  și Seminar )
# Aceasta este o tabelă de lookup (cautare) pentru țevi PEX/PPR (exemplu)
# Format: [Debit Max (l/s), Diametru Ext-Grosime (mm), Viteza (m/s), Pierdere (Pa/m)]
NOMOGRAMA_PPR = [
    # Vc_max, De-g,   v,   i (Pa/m)
    [0.20, "20-1.7", 0.9, 600],  # Aproximare din CSV pt 0.196 l/s
    [0.39, "25-1.9", 1.0, 650],  # Aproximare din CSV pt 0.382 l/s
    [0.55, "32-2.2", 0.9, 475],  # Aproximare din CSV pt 0.540 l/s
    [1.10, "40-2.4", 1.1, 420],  # Aproximare din CSV pt 1.046 l/s
    [2.00, "50-2.9", 1.2, 375],  # Aproximare din CSV pt 1.971 l/s
    [3.50, "63-3.6", 1.4, 350],  # Valori adaugate
    [6.00, "75-4.3", 1.7, 400],  # Valori adaugate
    [9.50, "90-5.1", 1.9, 450]   # Valori adaugate
]

# ======================================================================
# PARTEA 2: FUNCȚII HELPER
# ======================================================================

def get_dimensiune_teava(Vc):
    """
    Simulează căutarea pe nomogramă.
    Găsește prima țeavă care poate duce debitul Vc, respectând vitezele economice.
    """
    for teava in NOMOGRAMA_PPR:
        if Vc <= teava[0]:
            return {
                'De_g': teava[1],
                'v': teava[2],
                'i': teava[3]
            }
    # Daca debitul e mai mare decat ce avem in nomograma
    return {'De_g': "PREA MARE (>DN90)", 'v': -1, 'i': -1}

def add_fixture():
    """Adaugă un rând nou pentru un obiect sanitar în session_state."""
    new_id = st.session_state.next_id
    st.session_state.fixtures[new_id] = {'key': list(DATE_LOCUIT.keys())[0], 'count': 1}
    st.session_state.next_id += 1

def delete_fixture(id_to_delete):
    """Șterge un rând de obiect sanitar din session_state."""
    if id_to_delete in st.session_state.fixtures:
        del st.session_state.fixtures[id_to_delete]

# ======================================================================
# PARTEA 3: INTERFAȚA STREAMLIT
# ======================================================================

def run_app():
    st.set_page_config(page_title="Calculator I9", layout="centered")
    st.title("🚰 Calculator Dimensionare I9-2022")
    st.write("Realizat de **Gem de Sanitare** pe baza Normativului I9-2022.")

    # --- Inițializare Session State pentru rânduri dinamice ---
    if 'fixtures' not in st.session_state:
        # st.session_state.fixtures va fi un dicționar {id_unic: {key, count}}
        st.session_state.fixtures = {0: {'key': 'lavoar_princ', 'count': 1}}
    if 'next_id' not in st.session_state:
        st.session_state.next_id = 1

    # --- INPUTURI (în Sidebar) ---
    st.sidebar.header("1. Selectare Tronson")
    building_type_key = st.sidebar.selectbox(
        "Tip Clădire:",
        options=['locuit', 'alte'],
        format_func=lambda x: "Clădire de locuit (Metoda B)" if x == 'locuit' else "Alte clădiri (Metoda C)"
    )

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
    
    # Cream un container pentru formular
    form_container = st.container()
    
    fixture_keys = list(active_data.keys())
    fixture_names = [active_data[key]['nume'] for key in fixture_keys]

    # Parcurgem dictionarul de obiecte din session_state
    for fixture_id, fixture_data in st.session_state.fixtures.items():
        # Verificăm dacă cheia curentă mai există în setul de date activ
        # (se poate schimba dacă utilizatorul comută tipul clădirii)
        current_key = fixture_data['key']
        if current_key not in active_data:
            current_key = fixture_keys[0] # Resetăm la prima opțiune
            st.session_state.fixtures[fixture_id]['key'] = current_key

        current_index = fixture_keys.index(current_key)

        col1, col2, col3 = st.columns([4, 1, 1])
        
        # Coloana 1: Selectează obiectul
        selected_name = col1.selectbox(
            "Obiect Sanitar",
            options=fixture_names,
            index=current_index,
            key=f"select_{fixture_id}",
            label_visibility="collapsed"
        )
        # Salvăm cheia (nu numele) înapoi în state
        st.session_state.fixtures[fixture_id]['key'] = fixture_keys[fixture_names.index(selected_name)]
        
        # Coloana 2: Numărul de obiecte
        new_count = col2.number_input(
            "Cant.",
            min_value=1,
            value=fixture_data['count'],
            key=f"count_{fixture_id}",
            label_visibility="collapsed"
        )
        st.session_state.fixtures[fixture_id]['count'] = new_count
        
        # Coloana 3: Buton de ștergere
        col3.button("❌", key=f"del_{fixture_id}", on_click=delete_fixture, args=(fixture_id,))

    # Butonul de adăugare rând
    st.button("➕ Adaugă Obiect Sanitar", on_click=add_fixture)

    st.divider()

    # --- Butonul de Calcul și Afișarea Rezultatelor ---
    if st.button("Calculează Dimensionarea Tronsonului", type="primary", use_container_width=True):
        
        # Dicționar pentru a stoca rezultatele intermediare
        calcul_summary = {}
        
        # 1. Însumare totaluri
        N_total = 0
        U_total = 0
        E_total = 0
        Vs_total = 0
        Vc = 0.0 # Debitul de calcul final (l/s)

        for fixture_data in st.session_state.fixtures.values():
            key = fixture_data['key']
            count = fixture_data['count']
            
            if not key or count <= 0:
                continue

            N_total += count
            
            if building_type_key == 'locuit':
                data = DATE_LOCUIT[key]
                U_total += data['ui'] * count
                Vs_total += data['vs'] * count
            else: # 'alte'
                data = DATE_ALTE_CLADIRI[key]
                E_total += (data['e1'] + data['e2']) * count
        
        st.header("3. Rezultate Calcul")
        
        # 2. Aplicare logică de calcul I9
        if building_type_key == 'locuit':
            # --- METODA A & B (Locuit) ---
            calcul_summary["Metodă Aplicată"] = "Metoda B (Clădire de locuit)"
            calcul_summary["Total Unit. Consum (U)"] = f"{U_total:.2f}"
            calcul_summary["Total Obiecte (N)"] = N_total
            calcul_summary["Total Debit Specific (Vs_tot)"] = f"{Vs_total:.2f} l/s"

            # Calcul fAR 
            f_AR = 1.0
            if N_total > 1:
                f_AR = 0.83 / math.sqrt(N_total - 1)
            calcul_summary["Factor Simultan. (f_AR)"] = f"{f_AR:.4f}"

            if U_total < 15:
                # Verificare Metoda A [cite: 2907]
                Dmin_metodaA = -0.035 * (U_total**2) + 1.4 * U_total + 10.9
                st.info(f"**Verificare Metoda A (pentru U < 15):**\nDiametrul Minim Interior (Dmin) = **{Dmin_metodaA:.2f} mm**")

                # Calcul Metoda B.1 [cite: 777-781]
                if N_total == 1:
                    Vc = Vs_total
                else:
                    Vc = (Vs_total * f_AR) + 0.03
                calcul_summary["Calcul Vc (Metoda B.1)"] = f"({Vs_total:.2f} * {f_AR:.4f}) + 0.03"
            
            else:
                # Calcul Metoda B.2 
                Vc = Vs_total * f_AR
                calcul_summary["Calcul Vc (Metoda B.2)"] = f"{Vs_total:.2f} * {f_AR:.4f}"

        else:
            # --- METODA C (Alte Clădiri) ---
            formula_data = FORMULE_METODA_C[subtype_key]
            calcul_summary["Metodă Aplicată"] = f"Metoda C ({formula_data['nume']})"
            calcul_summary["Total Echivalenți (E)"] = f"{E_total:.2f}"
            
            if E_total < formula_data['min_e']:
                # Sub pragul minim 
                Vc = 0.2 * E_total
                calcul_summary["Calcul Vc"] = f"(E < {formula_data['min_e']}, Vc = 0.2 * E)"
            else:
                # Peste prag 
                Vc = formula_data['factor_e'] * math.sqrt(E_total)
                calcul_summary["Calcul Vc"] = f"({formula_data['factor_e']} * sqrt({E_total:.2f}))"
        
        calcul_summary["Debit de Calcul (Vc)"] = f"{Vc:.3f} l/s"

        # 3. Găsire Dimensiune (Simulare Nomogramă)
        teava = get_dimensiune_teava(Vc)
        
        # Afișare sumar
        st.subheader("Sumar Calcul:")
        st.json(calcul_summary)
        
        # Afișare rezultat final
        st.subheader("Rezultat Dimensionare:")
        if teava['v'] != -1:
            st.success(
                f"**Debit de Calcul (Vc): {Vc:.3f} l/s**\n\n"
                f"**Dimensiune Recomandată (PPR):**\n"
                f"- **Diametru (De-g): {teava['De_g']} mm**\n"
                f"- **Viteză (v): {teava['v']:.2f} m/s**\n"
                f"- **Pierdere Liniară (i): {teava['i']:.0f} Pa/m**"
            )
        else:
            st.error("Debitul de calcul este prea mare pentru nomograma predefinită (>DN90).")

# Punctul de intrare al aplicației
if __name__ == "__main__":
    run_app()