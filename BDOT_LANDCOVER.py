#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skrypt do automatycznej klasyfikacji i rasteryzacji danych BDOT10k.

Funkcjonalność:
1. Wyszukuje pliki GeoPackage (.gpkg) w folderze wejściowym na podstawie listy kodów BDOT.
2. Klasyfikuje obiekty zgodnie z zadanym schematem, z uwzględnieniem atrybutów dla lasów.
3. Scala wszystkie przetworzone warstwy w jeden plik wektorowy GeoPackage.
4. Rasteryzuje wynikową warstwę wektorową do formatu GeoTIFF (.tif).
"""

import os
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
import numpy as np # Dodano import numpy

# --- KONFIGURACJA ---
# Modyfikuj tylko te zmienne

# 1. Ścieżka do folderu z plikami BDOT10k (*.gpkg)
INPUT_FOLDER_PATH = "H:/Lukasz/6_MIASTA/7_PILA/1_dane/1_wektor/3_DBOT10k/"

# 2. Ścieżki do plików wynikowych
OUTPUT_VECTOR_PATH = "C:/Users/dawids/Desktop/PRACA/PROJEKTY/7_PILA/2025/LANDCOVER_BDOT/pila_klasyfikacja_v2.gpkg"
OUTPUT_RASTER_PATH = "C:/Users/dawids/Desktop/PRACA/PROJEKTY/7_PILA/2025/LANDCOVER_BDOT/pila_klasyfikacja_v2.tif"

# 3. Kody BDOT do przetworzenia
TARGET_BDOT_CODES = [
    "OT_PTTR_A", "OT_PTRK_A", "OT_PTPL_A", "OT_PTNZ_A",
    "OT_PTLZ_A", "OT_PTKM_A", "OT_PTGN_A", "OT_PTZB_A",
    "OT_PTWZ_A", "OT_PTWP_A", "OT_PTUT_A"
]

# 4. Mapa klasyfikacji: { kod BDOT: (ID_klasy, Nazwa_klasy) }
#    Uwaga: ID_klasy będzie wartością piksela w rastrze wynikowym.
#    Logika dla OT_PTLZ_A (Lasy) jest teraz obsługiwana bezpośrednio w kodzie.
CLASSIFICATION_MAP = {
    # Klasa 1: Paved (Nawierzchnie utwardzone)
    "OT_PTRK_A": (1, "Paved"),      # Kompleksy komunikacyjne
    "OT_PTPL_A": (1, "Paved"),      # Place
    "OT_PTUT_A": (1, "Paved"),      # Tereny urządzone i przekształcone

    # Klasa 2: Buildings (Budynki)
    "OT_PTZB_A": (2, "Buildings"),  # Tereny zabudowane

    # Klasa 3: Evergreen Trees (Drzewa iglaste) - przypisywana dynamicznie z OT_PTLZ_A
    # Klasa 4: Deciduous Trees (Drzewa liściaste) - przypisywana dynamicznie z OT_PTLZ_A

    # Klasa 5: Grass (Trawa)
    "OT_PTTR_A": (5, "Grass"),      # Trawiaste
    "OT_PTGN_A": (5, "Grass"),      # Tereny zieleni

    # Klasa 6: Bare soil (Gleba bez roślinności)
    "OT_PTNZ_A": (6, "Bare soil"),  # Nieużytki
    "OT_PTKM_A": (6, "Bare soil"),  # Tereny kamieniste

    # Klasa 7: Water (Woda)
    "OT_PTWP_A": (7, "Water"),      # Wody płynące
    "OT_PTWZ_A": (7, "Water"),      # Wody stojące
}

# 5. Rozdzielczość przestrzenna wynikowego rastra w metrach
RASTER_RESOLUTION_METERS = 1.0

# --- KONIEC KONFIGURACJI ---


def find_files_to_process(folder: str, codes: list) -> list:
    """Wyszukuje pliki GPKG pasujące do podanych kodów BDOT."""
    found_files = []
    print(f"INFO: Przeszukiwanie folderu: {folder}")
    for filename in os.listdir(folder):
        if filename.endswith(".gpkg") and any(code in filename for code in codes):
            full_path = os.path.join(folder, filename)
            found_files.append(full_path)
            print(f"  -> Znaleziono plik: {filename}")

    if not found_files:
        print("BŁĄD: Nie znaleziono żadnych pasujących plików .gpkg. Sprawdź ścieżkę i kody.")
    return found_files

def get_bdot_code_from_filename(filename: str, codes: list) -> str | None:
    """Wyodrębnia kod BDOT z nazwy pliku."""
    for code in codes:
        if code in filename:
            return code
    return None

# --- GŁÓWNA LOGIKA SKRYPTU ---

# Krok 1: Wybierz dane z BDOT
files_to_process = find_files_to_process(INPUT_FOLDER_PATH, TARGET_BDOT_CODES)
if not files_to_process:
    print("Brak plików do przetworzenia. Zakończono.")
    exit()

# Krok 2 i 3: Klasyfikacja i generowanie jednej warstwy wektorowej
print("\nINFO: Rozpoczynam przetwarzanie wektorowe...")
all_gdfs = []

for fpath in files_to_process:
    try:
        fname = os.path.basename(fpath)
        print(f"  -> Przetwarzam: {fname}")
        bdot_code = get_bdot_code_from_filename(fname, TARGET_BDOT_CODES)

        # NOWA LOGIKA: Specjalna obsługa dla warstwy lasów (OT_PTLZ_A)
        if bdot_code == "OT_PTLZ_A":
            gdf = gpd.read_file(fpath)
            if 'KATEGORIA' in gdf.columns:
                conditions = [
                    gdf['KATEGORIA'] == 'iglasty',
                    gdf['KATEGORIA'] == 'liściasty',
                    gdf['KATEGORIA'] == 'mieszany'
                ]
                class_ids = [3, 4, 4] # 3: Iglaste, 4: Liściaste, 4: Mieszane jako liściaste
                class_names = ["Evergreen Trees", "Deciduous Trees", "Deciduous Trees"]

                gdf['class_id'] = np.select(conditions, class_ids, default=0)
                gdf['class_name'] = np.select(conditions, class_names, default="Unknown")

                # Usuń obiekty, których nie udało się sklasyfikować
                unknown_count = len(gdf[gdf['class_id'] == 0])
                if unknown_count > 0:
                    print(f"     OSTRZEŻENIE: Znaleziono i pominięto {unknown_count} obiektów bez rozpoznanej kategorii w {fname}.")
                    gdf = gdf[gdf['class_id'] != 0].copy()
                
                if not gdf.empty:
                    all_gdfs.append(gdf)

            else:
                print(f"     OSTRZEŻENIE: Pomijam plik {fname}, brak wymaganej kolumny 'KATEGORIA'.")

        # Logika dla pozostałych warstw (bez zmian)
        elif bdot_code and bdot_code in CLASSIFICATION_MAP:
            gdf = gpd.read_file(fpath)
            class_id, class_name = CLASSIFICATION_MAP[bdot_code]
            gdf['class_id'] = class_id
            gdf['class_name'] = class_name
            all_gdfs.append(gdf)
        else:
            print(f"     OSTRZEŻENIE: Pomijam plik, brak reguły klasyfikacji dla kodu w pliku {fname}")

    except Exception as e:
        print(f"BŁĄD podczas przetwarzania pliku {fpath}: {e}")

if not all_gdfs:
    print("BŁĄD: Nie udało się przetworzyć żadnych warstw. Zakończono.")
    exit()

print("\nINFO: Łączenie warstw w jeden plik GeoPackage...")
merged_gdf = gpd.GeoDataFrame(pd.concat(all_gdfs, ignore_index=True))
merged_gdf.crs = all_gdfs[0].crs

os.makedirs(os.path.dirname(OUTPUT_VECTOR_PATH), exist_ok=True)
merged_gdf.to_file(OUTPUT_VECTOR_PATH, driver='GPKG')
print(f"SUKCES: Zapisano połączoną warstwę wektorową do: {OUTPUT_VECTOR_PATH}")

# Krok 4: Generowanie rastra (TIF)
print("\nINFO: Rozpoczynam rasteryzację...")
shapes = ((geom, value) for geom, value in zip(merged_gdf.geometry, merged_gdf['class_id']))

bounds = merged_gdf.total_bounds
width = int((bounds[2] - bounds[0]) / RASTER_RESOLUTION_METERS)
height = int((bounds[3] - bounds[1]) / RASTER_RESOLUTION_METERS)
transform = from_origin(bounds[0], bounds[3], RASTER_RESOLUTION_METERS, RASTER_RESOLUTION_METERS)

meta = {
    'driver': 'GTiff',
    'height': height,
    'width': width,
    'count': 1,
    'dtype': rasterio.uint8,
    'crs': merged_gdf.crs,
    'transform': transform,
    'nodata': 0
}

os.makedirs(os.path.dirname(OUTPUT_RASTER_PATH), exist_ok=True)
with rasterio.open(OUTPUT_RASTER_PATH, 'w', **meta) as out:
    burned_array = rasterize(
        shapes=shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype=rasterio.uint8
    )
    out.write(burned_array, 1)

print(f"SUKCES: Zapisano wynikowy raster do: {OUTPUT_RASTER_PATH}")
print("\nINFO: Zakończono pomyślnie.")
