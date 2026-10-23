-- Consultas do painel de métricas (PostHog, ferramenta execute-sql). Rode as duas e salve a saída de texto
-- (linhas separadas por |, com a linha de cabeçalho) em arquivos, depois: python3 src/painel.py agregado.txt diario.txt

-- [1] agregado
WITH base AS (
  SELECT
    toDate(toTimeZone(timestamp, 'America/Sao_Paulo')) AS dia,
    toDate(toTimeZone(now(), 'America/Sao_Paulo')) AS hoje,
    event,
    properties.$session_id AS sid,
    coalesce(nullIf(session.$entry_utm_source, ''), session.$entry_referring_domain, '$direct') AS origem,
    coalesce(properties.$device_type, '?') AS disp,
    concat(coalesce(properties.$geoip_city_name, '?'), ' - ', coalesce(properties.$geoip_subdivision_1_code, '')) AS cidade,
    coalesce(multiIf(
      event = 'aba_aberta', properties.aba,
      event = 'clique_prova', properties.prova,
      event = 'compartilhar_prova', properties.prova,
      event IN ('clique_parceiro', 'cupom_copiado'), properties.parceiro,
      event = 'clique_loja', properties.detalhe,
      event = 'seguir_instagram', properties.botao,
      event = 'compartilhar_link', properties.canal,
      event = 'calc_calculo', properties.modo,
      event = 'estado_escolhido', properties.estado,
      event = 'clique_calculadora', properties.origem,
      event = '$pageview', properties.$pathname,
      ''), '') AS chave
  FROM events
  WHERE timestamp >= now() - INTERVAL 92 DAY
    AND event IN ('$pageview', 'aba_aberta', 'clique_prova', 'compartilhar_prova', 'clique_parceiro', 'cupom_copiado',
                  'clique_loja', 'seguir_instagram', 'compartilhar_link', 'compartilhar_imagem', 'compartilhar_oferta',
                  'calc_calculo', 'estado_escolhido', 'clique_calculadora', 'abriu_link_compartilhado')
)
SELECT tupleElement(x, 1) AS p, tupleElement(x, 2) AS dim, tupleElement(x, 3) AS rotulo,
       uniq(sid) AS visitas, count() AS vezes
FROM (
  SELECT sid, arrayJoin(arrayFlatten(arrayMap(q -> arrayMap(t -> (q, tupleElement(t, 1), tupleElement(t, 2)),
             if(startsWith(q, 'ant'), [('evento', event)],
                if(event = '$pageview',
                   [('evento', event), ('origem', origem), ('disp', disp), ('cidade', cidade), ('pagina', chave)],
                   [('evento', event), (event, chave)]))),
           arrayFilter(q -> (q = 'hoje' AND dia = hoje)
                         OR (q = '7' AND dia > hoje - 7)
                         OR (q = '30' AND dia > hoje - 30)
                         OR (q = '90' AND dia > hoje - 90)
                         OR (q = 'ant7' AND dia <= hoje - 7 AND dia > hoje - 14)
                         OR (q = 'ant30' AND dia <= hoje - 30 AND dia > hoje - 60),
                       ['hoje', '7', '30', '90', 'ant7', 'ant30'])))) AS x
  FROM base
)
GROUP BY p, dim, rotulo
ORDER BY p, dim, visitas DESC, vezes DESC
LIMIT 20 BY p, dim
LIMIT 500

-- [2] diario
SELECT toDate(toTimeZone(timestamp, 'America/Sao_Paulo')) AS dia, uniq(properties.$session_id) AS visitas, uniqIf(properties.$session_id, coalesce(nullIf(session.$entry_utm_source, ''), session.$entry_referring_domain, '') IN ('ig', 'l.instagram.com', 'instagram.com', 'www.instagram.com')) AS instagram FROM events WHERE timestamp >= now() - INTERVAL 92 DAY AND event = '$pageview' GROUP BY dia ORDER BY dia LIMIT 100
