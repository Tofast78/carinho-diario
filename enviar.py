#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Envia a mensagem do dia (ou uma extra) por email e regista o envio em docs/registo.json.

Nome, assinatura e horas ficam no config.json.
Os emails e a palavra-passe vão nos Secrets do GitHub, para o repositório
poder ser público sem expor os endereços:
  SMTP_USER      - o teu email (remetente)
  SMTP_PASS      - palavra-passe de aplicação (NÃO a do Gmail)
  EMAIL_DESTINO  - o email dela
"""

import json
import os
import random
import smtplib
import ssl
import sys
import argparse
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent
MENSAGENS = RAIZ / "docs" / "mensagens.json"
REGISTO = RAIZ / "docs" / "registo.json"
CONFIG = RAIZ / "config.json"

with open(CONFIG, encoding="utf-8") as f:
    cfg = json.load(f)

FUSO = ZoneInfo(cfg.get("fuso", "Europe/Lisbon"))
HORA_ENVIO = int(cfg.get("hora_envio", 13))
MINUTO_ENVIO = int(cfg.get("minuto_envio", 5))
NOME_DELA = cfg["nome_dela"]
ASSINATURA = cfg.get("assinatura", "O teu marido")

CORES = {
    "carinho": "#B98BC9",
    "amor": "#FF6F91",
    "picante": "#E8B94A",
}
ETIQUETAS = {"carinho": "carinho", "amor": "amor", "picante": "picante"}


def carregar(caminho, omissao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return omissao


def escolher_mensagem(mensagens, registo, agora, tipo):
    """Escolhe a mensagem a enviar."""
    chave_data = agora.strftime("%m-%d")

    if tipo == "diaria":
        # 1) data especial (Natal, Ano Novo, etc.)
        for m in mensagens:
            if m.get("data") == chave_data:
                return m
        # 2) mensagem correspondente ao dia do ano (descontando os dias especiais)
        candidatas = [m for m in mensagens if not m.get("data")]
        dia = agora.timetuple().tm_yday
        especiais = []
        for m in mensagens:
            if m.get("data"):
                mes, d = m["data"].split("-")
                especiais.append(datetime(agora.year, int(mes), int(d)).timetuple().tm_yday)
        indice = dia - 1 - sum(1 for e in especiais if e < dia)
        if indice < len(candidatas):
            return candidatas[indice]
        return random.choice(candidatas)  # dia 366 nos anos bissextos

    # extras: por tipo ou aleatória, evitando as últimas 60 enviadas
    recentes = {e.get("id") for e in registo[:60]}
    pool = [m for m in mensagens if tipo in ("aleatoria", m["tipo"])]
    frescas = [m for m in pool if m["id"] not in recentes] or pool
    return random.choice(frescas)


def corpo_html(m, agora, extra):
    cor = CORES.get(m["tipo"], "#FF6F91")
    selo = "mensagem extra" if extra else agora.strftime("%d/%m/%Y")
    return f"""<!doctype html>
<html lang="pt"><body style="margin:0;padding:28px 16px;background:#241428;font-family:Georgia,'Times New Roman',serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
    <table role="presentation" width="100%" style="max-width:520px;background:#2F1B34;border-radius:20px;border:1px solid #4A2B52;">
      <tr><td style="padding:30px 30px 10px 30px;">
        <div style="font-family:Helvetica,Arial,sans-serif;font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:{cor};">
          {ETIQUETAS.get(m['tipo'], m['tipo'])} &nbsp;·&nbsp; {selo}
        </div>
      </td></tr>
      <tr><td style="padding:6px 30px 26px 30px;">
        <p style="margin:0 0 18px 0;font-size:17px;color:#F5E9E2;">Olá {NOME_DELA} 💗</p>
        <p style="margin:0;font-size:23px;line-height:1.5;color:#FDF3EC;">{m['texto']}</p>
      </td></tr>
      <tr><td style="padding:0 30px 30px 30px;">
        <div style="height:1px;background:#4A2B52;margin-bottom:16px;"></div>
        <div style="font-family:Helvetica,Arial,sans-serif;font-size:13px;color:#C9A7D4;">
          {ASSINATURA} &nbsp;•&nbsp; {agora.strftime('%H:%M')} ❤️
        </div>
      </td></tr>
    </table>
    <div style="font-family:Helvetica,Arial,sans-serif;font-size:11px;color:#7A5C82;padding-top:14px;">
      mensagem {m['id']} de 365 🌹
    </div>
  </td></tr></table>
</body></html>"""


def enviar_email(m, agora, extra):
    host = cfg.get("smtp_host", "smtp.gmail.com")
    porta = int(cfg.get("smtp_porta", 465))
    utilizador = os.environ.get("SMTP_USER") or cfg.get("teu_email")
    destino = os.environ.get("EMAIL_DESTINO") or cfg.get("email_dela")
    senha = os.environ.get("SMTP_PASS")
    em_falta = [n for n, v in
                (("SMTP_USER", utilizador), ("EMAIL_DESTINO", destino), ("SMTP_PASS", senha))
                if not v]
    if em_falta:
        raise SystemExit("Faltam estes Secrets no GitHub: " + ", ".join(em_falta))

    msg = EmailMessage()
    msg["Subject"] = ("💌 Uma mensagem só para ti" if extra
                      else f"💗 Para ti, {NOME_DELA} — {agora.strftime('%d/%m')}")
    msg["From"] = formataddr((ASSINATURA, utilizador))
    msg["To"] = destino
    msg.set_content(f"{m['texto']}\n\n— {ASSINATURA}")
    msg.add_alternative(corpo_html(m, agora, extra), subtype="html")

    contexto = ssl.create_default_context()
    if porta == 465:
        with smtplib.SMTP_SSL(host, porta, context=contexto) as s:
            s.login(utilizador, senha)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, porta) as s:
            s.starttls(context=contexto)
            s.login(utilizador, senha)
            s.send_message(msg)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tipo", default="diaria",
                   choices=["diaria", "aleatoria", "carinho", "amor", "picante"])
    p.add_argument("--forcar", action="store_true", help="ignora a verificação da hora")
    args = p.parse_args()

    agora = datetime.now(FUSO)
    mensagens = carregar(MENSAGENS, [])
    registo = carregar(REGISTO, [])
    if not mensagens:
        print("Não encontrei mensagens.json"); sys.exit(1)

    extra = args.tipo != "diaria"

    if not extra and not args.forcar:
        # O GitHub corre os workflows em UTC e costuma atrasar-se uns minutos.
        # Enviamos se já passou a hora certa em Portugal, dentro de uma janela de 90 min.
        atraso = (agora.hour * 60 + agora.minute) - (HORA_ENVIO * 60 + MINUTO_ENVIO)
        if not 0 <= atraso <= 90:
            print(f"Agora são {agora:%H:%M} em Portugal. Envio é às "
                  f"{HORA_ENVIO:02d}:{MINUTO_ENVIO:02d}. A sair.")
            return
        hoje = agora.strftime("%Y-%m-%d")
        if any(e["quando"].startswith(hoje) and not e.get("extra") for e in registo):
            print("A mensagem de hoje já foi enviada. A sair.")
            return

    m = escolher_mensagem(mensagens, registo, agora, args.tipo)
    enviar_email(m, agora, extra)

    registo.insert(0, {
        "id": m["id"],
        "tipo": m["tipo"],
        "texto": m["texto"],
        "quando": agora.isoformat(timespec="seconds"),
        "data": agora.strftime("%Y-%m-%d"),
        "hora": agora.strftime("%H:%M"),
        "extra": extra,
    })
    REGISTO.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTO, "w", encoding="utf-8") as f:
        json.dump(registo[:1000], f, ensure_ascii=False, indent=2)

    print(f"Enviada a mensagem {m['id']} ({m['tipo']}) às {agora:%H:%M}.")


if __name__ == "__main__":
    main()
