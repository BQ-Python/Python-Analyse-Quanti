import pandas as pd
import os
import numpy as np
from scipy.optimize import minimize

# Chemin du fichier
repo_path = "Hedging/data.xlsx"
if not os.path.exists(repo_path):
    raise FileNotFoundError(f"Le fichier {repo_path} n'existe pas. Vérifiez le chemin.")

# Charger le fichier Excel
df = pd.read_excel(repo_path)

# Vérifier les colonnes requises
required_columns = [
    "quotationDate", 
    "EURIBOR1M", "EURIBOR3M", "EURIBOR6M", "EURIBOR1Y",
    "USDSOFR1M", "USDSOFR3M", "USDSOFR6M", "USDSOFR1Y",
    "EUR/USD spot"
]
if not all(col in df.columns for col in required_columns):
    raise ValueError("Colonnes manquantes dans le fichier Excel.")

# Fonction pour calculer le taux forward
def calculate_forward_rate(spot, r_usd, r_eur, days):
    return spot * (1 + (r_usd / 100) * days / 360) / (1 + (r_eur / 100) * days / 360)

# Fonction du modèle Nelson-Siegel-Svensson
def nss_model(t, beta0, beta1, beta2, beta3, tau1, tau2):
    t = np.array(t)
    term1 = beta0
    term2 = beta1 * (1 - np.exp(-t / tau1)) / (t / tau1)
    term3 = beta2 * ((1 - np.exp(-t / tau1)) / (t / tau1) - np.exp(-t / tau1))
    term4 = beta3 * ((1 - np.exp(-t / tau2)) / (t / tau2) - np.exp(-t / tau2))
    return term1 + term2 + term3 + term4

# Fonction d'erreur pour l'ajustement NSS
def nss_error(params, t, rates):
    beta0, beta1, beta2, beta3, tau1, tau2 = params
    predicted_rates = nss_model(t, beta0, beta1, beta2, beta3, tau1, tau2)
    return np.sum((predicted_rates - rates) ** 2)

# Fonction pour extrapoler les taux à 2 ans avec NSS
def extrapolate_rate_nss(row, rate_cols, maturities_years):
    rates = np.array([row[col] for col in rate_cols])
    # Initialisation des paramètres
    initial_params = [2.0, -1.0, 1.0, 1.0, 0.5, 1.0]  # [beta0, beta1, beta2, beta3, tau1, tau2]
    # Minimisation pour ajuster les paramètres
    result = minimize(
        nss_error,
        initial_params,
        args=(maturities_years, rates),
        method='L-BFGS-B',
        bounds=[(0, 10), (-10, 10), (-10, 10), (-10, 10), (0.1, 5), (0.1, 5)]
    )
    beta0, beta1, beta2, beta3, tau1, tau2 = result.x
    # Extrapoler à 2 ans (t = 2)
    return nss_model(2, beta0, beta1, beta2, beta3, tau1, tau2)

# Définir les maturités et colonnes associées
maturities = {
    "1M": {"days": 30, "years": 30/360, "euribor": "EURIBOR1M", "sofr": "USDSOFR1M"},
    "3M": {"days": 90, "years": 90/360, "euribor": "EURIBOR3M", "sofr": "USDSOFR3M"},
    "6M": {"days": 180, "years": 180/360, "euribor": "EURIBOR6M", "sofr": "USDSOFR6M"},
    "1Y": {"days": 360, "years": 1.0, "euribor": "EURIBOR1Y", "sofr": "USDSOFR1Y"},
    "2Y": {"days": 720, "years": 2.0, "euribor": "EURIBOR2Y", "sofr": "USDSOFR2Y"}
}

# Colonnes et maturités pour NSS
maturities_years = [30/360, 90/360, 180/360, 1.0]  # En années pour 1M, 3M, 6M, 1Y
euribor_cols = ["EURIBOR1M", "EURIBOR3M", "EURIBOR6M", "EURIBOR1Y"]
sofr_cols = ["USDSOFR1M", "USDSOFR3M", "USDSOFR6M", "USDSOFR1Y"]

# Ajouter des colonnes pour les taux extrapolés à 2 ans
df["EURIBOR2Y"] = df.apply(lambda row: extrapolate_rate_nss(row, euribor_cols, maturities_years), axis=1)
df["USDSOFR2Y"] = df.apply(lambda row: extrapolate_rate_nss(row, sofr_cols, maturities_years), axis=1)

# Calculer les taux forward pour toutes les maturités
for maturity, info in maturities.items():
    df[f"Forward_{maturity}"] = df.apply(
        lambda row: calculate_forward_rate(
            row["EUR/USD spot"], 
            row[info["sofr"]], 
            row[info["euribor"]], 
            info["days"]
        ), axis=1
    )

# Formater les colonnes numériques avec des virgules pour la sortie
numeric_cols = euribor_cols + sofr_cols + ["EUR/USD spot", "EURIBOR2Y", "USDSOFR2Y"] + [f"Forward_{m}" for m in maturities]
for col in numeric_cols:
    df[col] = df[col].apply(lambda x: f"{x:.6f}".replace(".", ","))

# Sauvegarder les résultats dans un nouveau fichier Excel
output_path = "/Python-Analyse-Quanti/Hedging/data_with_forwards.xlsx"
df.to_excel(output_path, index=False)

# Afficher un aperçu des résultats
print(f"Résultats sauvegardés dans {output_path}")
print("\nAperçu des premières lignes :")
print(df[["quotationDate", "EUR/USD spot", "Forward_1M", "Forward_3M", "Forward_6M", "Forward_1Y", "Forward_2Y"]].head())
