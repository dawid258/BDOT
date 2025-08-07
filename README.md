SCRIPT change bdot layers to landcover .tif and landcover vector file.
TARGET_BDOT_CODES = 

    "OT_PTTR_A", "OT_PTRK_A", "OT_PTPL_A", "OT_PTNZ_A",
    "OT_PTLZ_A", "OT_PTKM_A", "OT_PTGN_A", "OT_PTZB_A",
    "OT_PTWZ_A", "OT_PTWP_A", "OT_PTUT_A"


CLASSIFICATION_MAP = 
{

    # Klasa 1: Paved (Nawierzchnie utwardzone)
    "OT_PTRK_A": (1, "Paved"),  # Kompleksy komunikacyjne
    "OT_PTPL_A": (1, "Paved"),  # Place
    "OT_PTUT_A": (1, "Paved"),  # Tereny urządzone i przekształcone
    # Klasa 2: Buildings (Budynki)
    "OT_PTZB_A": (2, "Buildings"), # Tereny zabudowane
    # Klasa 3: Evergreen Trees (Drzewa iglaste) - BDOT10k nie różnicuje, łączymy
    "OT_PTLZ_A": (3, "Evergreen Trees"), # Lasy
    # Klasa 4: Deciduous Trees (Drzewa liściaste) - BDOT10k nie różnicuje, łączymy
    # Tu można by próbować różnicować na podstawie atrybutów, jeśli istnieją.
    # Na razie przypisujemy do jednej klasy drzew.
    
    # Klasa 5: Grass (Trawa)
    "OT_PTTR_A": (5, "Grass"), # Trawiaste
    "OT_PTGN_A": (5, "Grass"), # Tereny zieleni
    
    # Klasa 6: Bare soil (Gleba bez roślinności)
    "OT_PTNZ_A": (6, "Bare soil"), # Nieużytki
    
    # Klasa 7: Water (Woda)
    "OT_PTWP_A": (7, "Water"), # Wody płynące
    "OT_PTWZ_A": (7, "Water"), # Wody stojące
    
    # Kody, które mogą być problematyczne lub wymagać ręcznej weryfikacji
    "OT_PTKM_A": (6, "Bare soil") # Tereny kamieniste - przypisano do "Bare soil"
}
