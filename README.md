# Radar diário de corrida da Aline

Site do radar da @amartinscc: provas de corrida, parceiros (cupom AMARTINS) e ofertas de tênis de corrida.

- `index.html`: o site. Os dados ficam no bloco `<script id="radar-data" type="application/json">`, atualizado automaticamente todos os dias.
- `src/template.html`: layout do site. Depois de mudar o layout, rode `python3 src/build.py` para regerar o `index.html` mantendo os dados.
