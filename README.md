# Binance Futures Testnet Trading Bot

A Python command-line application for placing **MARKET** and **LIMIT** orders (BUY and SELL) on the Binance USDT-M Futures Testnet.

The project focuses on clean code, input validation, logging, and error handling rather than trading strategies.

---

## Features

- Places **MARKET** and **LIMIT** orders on Binance USDT-M Futures Testnet
- Supports both **BUY** and **SELL** sides
- CLI input for `symbol`, `side`, `type`, `quantity`, and `price` (LIMIT only)
- Validates and normalizes all user input (case-insensitive, trims whitespace)
- Automatically rounds quantity/price to each symbol's **step size** / **tick size**
  so orders don't get rejected for precision
- Prints a clean **order request summary** and **order response details**
  (`orderId`, `status`, `executedQty`, `avgPrice` if available)
- Clear **success / failure** messages and correct process **exit codes**
- Logs all API requests, responses, and errors to a rotating log file
- Graceful exception handling (invalid input, API errors, network failures)
- Modular architecture with separated client / service / CLI layers

---

## Project structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── config.py           
│   ├── exceptions.py       
│   ├── logging_config.py   
│   ├── client.py          
│   ├── validators.py       
│   └── orders.py           
├── logs/
│   └── trading_bot.log     
├── cli.py                  
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

**Design in one line:** `cli.py` (parse + present) → `orders.py` (workflow) →
`client.py` (Binance I/O), with `config`, `validators`, `logging_config`, and
`exceptions` as shared foundations. Only `client.py` imports `python-binance`.

---

## Prerequisites

- **Python 3.9+**
- A **Binance Futures Testnet (Demo Trading)** account and API credentials
  (see setup below — the testnet uses fake funds and requires no deposit)

---

## Setup

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd trading_bot
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Binance Futures Testnet API credentials

1. Go to **https://testnet.binancefuture.com** (this now redirects through
   Binance **Demo Trading** and asks you to log in with a Binance account).
2. Log in / register, then click **Start demo trading**. The demo account is
   auto-funded with test USDT — **no deposit or KYC is required for the demo key**.
3. On the demo futures page, scroll to the bottom and open the **API Key** panel.
4. Generate a **HMAC-SHA256** (system-generated) key and copy the **API Key** and
   **Secret Key** (the secret is shown only once).

### 5. Configure your credentials

```bash
cp .env.example .env
```

Then edit `.env` and paste your keys:

```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
BINANCE_TESTNET_BASE_URL=https://testnet.binancefuture.com
```

`.env` is git-ignored and must **never** be committed.

---

## Usage

Run from the **project root**.

### Place a MARKET order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.002
```

### Place a LIMIT order (price required)

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.002 --price 65000
```

### Verbose mode (show full request/response on the console)

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.002 --verbose
```

### Help

```bash
python cli.py --help
```

### Arguments

| Argument      | Required           | Description                                        |
|---------------|--------------------|----------------------------------------------------|
| `--symbol`    | yes                | Trading pair, e.g. `BTCUSDT`                        |
| `--side`      | yes                | `BUY` or `SELL` (case-insensitive)                 |
| `--type`      | yes                | `MARKET` or `LIMIT` (case-insensitive)             |
| `--quantity`  | yes                | Order size in the base asset (e.g. `0.002`)        |
| `--price`     | LIMIT only         | Limit price; ignored for MARKET                    |
| `--verbose`   | no                 | Show DEBUG-level detail on the console             |

---

## Example output

```
──────── ORDER REQUEST ────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.002
───────────────────────────────
──────── ORDER RESPONSE ───────
  Order ID     : 4021997663
  Status       : FILLED
  Orig Qty     : 0.002
  Executed Qty : 0.002
  Avg Price    : 65012.30
───────────────────────────────

✅ SUCCESS: order placed.
```

A LIMIT order that rests (does not fill immediately) shows `Status: NEW`,
`Executed Qty: 0`, and `Avg Price: n/a`.

---

## Logging

- All logs are written to **`logs/trading_bot.log`**.
- Use `--verbose` to display DEBUG logs in the console.
- API credentials are never logged.

Sample log files from a MARKET order and a LIMIT order are included with this
submission (see the `logs/` directory).

---

## Error handling

The app fails gracefully with a clear message and a non-zero exit code:

- **Invalid input** (bad side/type, missing LIMIT price, non-positive quantity,
  quantity below the symbol minimum) → `ValidationError`, caught before any API call.
- **Exchange rejection / API error** (invalid symbol, insufficient margin, etc.) →
  `OrderError`, wrapping the underlying Binance error.
- **Network failure** (timeout, connection error) → `OrderError`.
- **Missing configuration** (unset API key/secret) → `ConfigurationError` at startup.

Unexpected errors are logged with a traceback while a user-friendly message is displayed in the terminal.

---

## Assumptions

- **Testnet only.** The application targets the Binance Futures Testnet only.
- **One-way position mode.** The account is assumed to be in **One-way** mode (the
  default), not **Hedge** mode. In Hedge mode, Binance requires a `positionSide`
  parameter and orders would return error `-4061`; switch the demo account to
  One-way, or extend `create_order` to pass `positionSide`.
- **Time-in-force.** LIMIT orders use **GTC** (good-till-cancelled) by default.
- **Precision.** Quantity and price are rounded **down** to the symbol's step size
  and tick size using exact decimal arithmetic. A quantity below the symbol's
  minimum is rejected locally with a clear message.
- **Leverage/margin.** The demo account's existing leverage and margin settings are
  used as-is; the app does not change them.
- **Single order per invocation.** Each CLI run places exactly one order.

---

## Tech stack

- Python 3.13.3 (developed and tested)
- [`python-binance`](https://github.com/sammchardy/python-binance) — Binance API SDK
- [`python-dotenv`](https://github.com/theskumar/python-dotenv) — environment config
- `argparse`, `logging`, `decimal`, `dataclasses` — standard library

---

## Notes

Built as a coding assignment for a Python Developer application. The emphasis is on
clean structure, validation, logging, and error handling rather than trading logic.