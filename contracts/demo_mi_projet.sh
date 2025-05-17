
########################################
# 1) Création de l'ASA
########################################
echo "1) Création de l'ASA…"
python scripts/create_asa.py
echo
echo "IMPORTANT : un nouvel ASSET_ID a été généré."
echo "  • Ouvrez votre fichier .env et remplacez la valeur d’ASSET_ID par celle affichée ci-dessus."
echo "  • Redémarrez le serveur API :"
echo "      – Ctrl+C dans le terminal uvicorn"
echo "      – uvicorn service:app --reload"
echo "Appuyez sur [Entrée] pour continuer…"
read

########################################
# 2) Opt-in des comptes Burn/LP/Rewards
########################################
echo "2) Opt-in des comptes Burn, LP et Rewards…"
python scripts/optin_targets.py
echo "Opt-in terminé pour les comptes ciblés."
echo

########################################
# 3) Compilation et déploiement du smart-contract
########################################
echo "3) Compilation et déploiement du smart-contract…"
python tax_token.py
python scripts/deploy.py
echo
echo "IMPORTANT : un nouvel APP_ID a été généré."
echo "  • Ouvrez votre fichier .env et remplacez la valeur d’APP_ID par celle affichée ci-dessus."
echo "  • Redémarrez à nouveau le serveur API :"
echo "      – Ctrl+C"
echo "      – uvicorn service:app --reload"
echo "Appuyez sur [Entrée] pour continuer…"
read

########################################
# 4) Test de la taxe on-chain
########################################
echo "4) Exécution du test de la taxe on-chain…"
python tests/test_tax.py
echo

########################################
# 5) Lecture du solde de la treasury
########################################
echo "5) Lecture du solde de la treasury…"
curl http://127.0.0.1:8000/treasury-balance && echo

########################################
# 6) Redistribution manuelle (10/20/30)
########################################
echo "6) Redistribution manuelle (10/20/30)…"
curl -X POST http://127.0.0.1:8000/distribute-manual \
  -H "Content-Type: application/json" \
  -d '{"burn":10,"lp":20,"rewards":30}'
echo
echo "Solde mis à jour de la treasury :"
curl http://127.0.0.1:8000/treasury-balance && echo

########################################
# 7) Redistribution automatique (split 1/3)
########################################
echo "7) Redistribution automatique (répartition 1/3)…"
curl -X POST http://127.0.0.1:8000/distribute-all
echo
echo "Solde final de la treasury :"
curl http://127.0.0.1:8000/treasury-balance && echo

echo " Démo du backend mi-projet terminée !"
