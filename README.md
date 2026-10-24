# ReWater — Machine-learning decision support for safe wastewater reuse

Environmental Biotechnology project: *Wastewater Treatment in the Circular Economy:
Resource Recovery, Nutrient Removal, and Biotechnological Innovations.*

**Live app:** https://YOUR-APP-NAME.streamlit.app  (replace after deploying)

## What it does
| Page | Purpose |
|---|---|
| Effluent Predictor | Predicts effluent BOD, COD and TSS from plant readings (machine learning) |
| Reuse Checker | Compares effluent quality with Pakistan discharge limits and US EPA (2012) reuse guidelines |
| Resource Recovery | Estimates biogas, electricity, struvite fertiliser, nitrogen and PHA bioplastic |
| Learn & Survey | Explains risks (pathogens, ARGs, microplastics) and links to the perception survey |
| About the Model | Model performance and figures |

## Run it yourself
```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate      Mac/Linux:  source .venv/bin/activate
pip install -r requirements.txt
python src/prepare_data.py
python src/train_models.py
streamlit run app.py
```
Survey analysis (after exporting Google Form responses to `survey/responses.csv`):
```bash
python src/analyze_survey.py
```

## Data
Poch, M. (1993). *Water Treatment Plant* [Dataset]. UCI Machine Learning Repository.
https://doi.org/10.24432/C5FS4C (CC BY 4.0).

## Author
Hamad Ahmad — Institute of Space Technology, Islamabad.

## Licence
Code: MIT. Data: CC BY 4.0 (original authors).
