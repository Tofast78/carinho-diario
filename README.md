# Cartas diárias 💌

365 mensagens de carinho, amor e algumas picantes, enviadas por email uma por dia às **12:59** (hora de Portugal), com um painel online para ver o que já foi enviado e mandar uma mensagem extra quando quiser.

```
config.json           → nome, emails e hora (edita só isto)
mensagem-diaria.yml   → o relógio (GitHub Actions)
enviar.py             → escolhe a mensagem e envia o email
docs/mensagens.json   → as 365 mensagens (podes editar à vontade)
docs/registo.json     → o que já foi enviado (escrito automaticamente)
docs/index.html       → o painel de controlo
```

---

## 1. Criar o repositório

Cria um repositório no GitHub (ex.: `cartas`) e envia estes ficheiros para o ramo `main`.

**Público ou privado?** O painel usa o GitHub Pages, que em repositórios privados só funciona com GitHub Pro. Com conta gratuita, faz o repositório público: os emails e a palavra-passe estão nos Secrets e nunca aparecem: só ficam visíveis as mensagens.

## 2. Palavra-passe de aplicação do email

Com Gmail: ativa a verificação em dois passos na conta Google e cria uma **palavra-passe de aplicação** em <https://myaccount.google.com/apppasswords>. São 16 letras. Não uses a palavra-passe normal.

Outros fornecedores funcionam também — muda `smtp_host` e `smtp_porta` no `config.json`.

## 3. Configurar

No **`config.json`** ficam as coisas que não fazem mal a ninguém ver:

```json
{ "nome_dela": "Sónia", "assinatura": "Biju", "hora_envio": 12, "minuto_envio": 59 }
```

Os emails e a palavra-passe vão nos Secrets, para o repositório poder ser público:
**Settings → Secrets and variables → Actions → New repository secret** (três vezes)

| Nome | Valor |
|---|---|
| `SMTP_USER` | o teu email, que envia |
| `SMTP_PASS` | a palavra-passe de aplicação (16 letras) |
| `EMAIL_DESTINO` | o email dela |

> Nada disto deve ir para um ficheiro: o que entra no Git fica no histórico para sempre, mesmo depois de apagado.

**Settings → Actions → General → Workflow permissions:** escolhe **Read and write permissions**. É isto que deixa o registo ser guardado.

**Settings → Pages:** *Source* = `Deploy from a branch`, ramo `main`, pasta `/docs`. Um minuto depois o painel está em `https://oteuutilizador.github.io/cartas/`.

## 4. Testar

Vai a **Actions → Mensagem diária → Run workflow**, escolhe `aleatoria` e carrega em Run. Se o email chegar, está feito. A partir daí sai sozinha todos os dias às 13:05.

## 5. Botão de mensagem extra

O painel precisa de um token para pedir o envio ao GitHub:

1. <https://github.com/settings/personal-access-tokens/new> → **Fine-grained token**
2. *Repository access*: só o repositório das cartas
3. *Permissions → Repository permissions → Actions*: **Read and write**
4. Copia o token e cola-o no painel

O token fica só na memória da página, por isso tens de o colar de cada vez que abres o painel. É o mais seguro — se preferires a comodidade, guarda-o nas palavras-passe do telemóvel e cola com dois toques.

---

## Coisas úteis

**Mudar a hora:** muda `hora_envio` e `minuto_envio` no `config.json` **e** as duas linhas `cron` no `mensagem-diaria.yml`, que estão em UTC (o GitHub não trabalha noutro fuso). Para as 20:30, por exemplo: `hora_envio: 20`, `minuto_envio: 30`, `30 19 * * *` e `30 20 * * *`. O `enviar.py` confirma sempre a hora de Lisboa antes de enviar, por isso nunca sai duas vezes.

**O GitHub pode atrasar-se:** os agendamentos gratuitos saem por vezes alguns minutos depois da hora. O script aceita um atraso até 90 minutos e envia à mesma, sem repetir.

**Datas especiais:** as últimas 5 mensagens do `mensagens.json` têm um campo `data` (`"12-25"`, etc.) e mandam nesse dia, aconteça o que acontecer. Acrescenta o aniversário dela e o vosso aniversário de casamento da mesma maneira:

```json
{ "id": 366, "tipo": "amor", "data": "03-17", "texto": "Parabéns, meu amor. 🎂❤️" }
```

**Editar mensagens:** abre `docs/mensagens.json` e muda o que quiseres. Escreve como tu falas — vai soar melhor do que qualquer coisa que eu escreva.

**Agendamentos adormecidos:** o GitHub desliga o `cron` de repositórios sem atividade durante 60 dias. Como o próprio envio faz um commit todos os dias, isso não acontece.
