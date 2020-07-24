# tarok

Za delovanje potrebuje:
- Python3
- boltons: https://pypi.org/project/boltons/ (pip install boltons)
    razlog je iterutils.chunked(), ki razreže seznam na več podseznamov določene dolžine in jih vrne kot en seznam s podseznami

Play.py
Tole zaženeš, če hočeš igrati.


Environment.py
V bistvu je to objekt igre Tarok. Skrbi za vse podatke o igri in jih sporoča Agentom (igralcem). Če so podatki javni, jih sporoči vsem hkrati, sicer selektivno. Sprašuje agente o njihovih odločitvah, ko pride vrsta nanje.


Agent.py
Vsebuje tri agente:
- Agent_0: igra naključno. Primeren predvsem za testiranje.
- Agent_H: igra človek. 
- Agent_AI: agent, ki se uči. Ali pa znanje pobere preko Load metode. Včasih si pomega tudi s približki (naloži jih z isto metodo).
