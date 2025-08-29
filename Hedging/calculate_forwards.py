import pandas as pd
import os

# Définir le chemin du fichier
repo_path = "Python-Analyse-Quanti/Hedging/data.xlsx"
if not os.path.exists(repo_path):
    raise FileNotFoundError(f"Le fichier {repo_path} n'existe pas. Vérifiez le chemin.")

# Lire le fichier Excel
df = pd.read_excel(repo_path)

# Vérifier que les colonnes attendues sont présentes
required_columns = ["QuotationDate", "EURIBOR1M", "EURIBOR3M", "SR1M", "SR3M", "EUR/USD"]
if not all(col in df.columns for col in required_columns):
    raise ValueError("Certaines colonnes attendues sont manquantes dans le fichier Excel.")

# Fonction pour calculer le taux forward
def calculate_forward_rate(spot, r_usd, r_eur, days):
    return spot * (1 + (r_usd / 100) * days / 360) / (1 + (r_eur / 100) * days / 360)

# Calcul des taux forward pour 1 mois (30 jours) et 3 mois (90 jours)
df["Forward_1M"] = df.apply(
    lambda row: calculate_forward_rate(row["EUR/USD"], row["SR1M"], row["EURIBOR1M"], 30), axis=1
)
df["Forward_3M"] = df.apply(
    lambda row: calculate_forward_rate(row["EUR/USD"], row["SR3M"], row["EURIBOR3M"], 90), axis=1
)

# Sauvegarder les résultats dans un nouveau fichier Excel
output_path = "Python-Analyse-Quanti/Hedging/data_with_forwards.xlsx"
df.to_excel(output_path, index=False)

# Afficher un aperçu des résultats
print(df[["QuotationDate", "EUR/USD", "Forward_1M", "Forward_3M"]].head())

print(f"\nLes taux forward ont été calculés et sauvegardés dans {output_path}")
