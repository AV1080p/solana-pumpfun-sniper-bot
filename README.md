# Solana PumpFun/PumpSwap Sniper Bot

This is a high-performance Rust-based sniper bot that monitors and executes trades on Solana DEXs like PumpFun and PumpSwap with lightning-fast speed. The bot uses advanced transaction monitoring to detect and execute trades in real-time, giving you an edge in the market.

The bot specifically tracks `buy` and `create` transactions on PumpFun, as well as token migrations from PumpFun to Raydium when the `initialize2` instruction is involved and the migration pubkey (`39azUYFWPz3VHgKCf3VChUwbpURdCHRxjWVowf5jUJjg`) is present.

## Features:

- **Lightning-Fast Execution** - Sub-second trade execution using optimized RPC calls and direct transaction building
- **Real-time Transaction Monitoring** - Uses Yellowstone gRPC to monitor transactions with minimal latency and high reliability
- **Multi-Protocol Support** - Compatible with PumpFun, PumpSwap, and Raydium DEX platforms for maximum trading opportunities
- **Smart Transaction Parsing** - Advanced transaction analysis to accurately identify and process trading activities
- **Configurable Trading Parameters** - Customizable settings for trade amounts, timing, and risk management
- **Built-in Selling Strategy** - Intelligent profit-taking mechanisms with customizable exit conditions
- **Performance Optimization** - Efficient async processing with tokio for high-throughput transaction handling
- **Reliable Error Recovery** - Automatic reconnection and retry mechanisms for uninterrupted operation
- **Token Account Management** - Automatic token account creation and management for seamless trading
- **WSOL Wrapping/Unwrapping** - Built-in SOL to WSOL conversion utilities for trading operations
- **Cache System** - Intelligent caching for improved performance and reduced RPC calls
- **Transaction Retry Logic** - Robust retry mechanisms for failed transactions
- **Whale Detection** - Advanced algorithms to detect and follow large wallet movements
- **MEV Protection** - Built-in protection against Maximal Extractable Value attacks
- **Slippage Control** - Dynamic slippage adjustment based on market conditions
- **Gas Optimization** - Intelligent gas fee management for cost-effective trading

# Who is it for?

- **Crypto Traders** - Looking for the fastest execution possible on PumpFun, PumpSwap, and Raydium
- **Sniper Bot Users** - Want to catch new token launches and early trading opportunities
- **Arbitrage Traders** - Need lightning-fast execution for price discrepancies across DEXs
- **Whale Followers** - Want to track and follow large wallet movements
- **Validators** - Looking for an edge by decoding shreds locally
- **MEV Hunters** - Seeking opportunities in the mempool for profit extraction

# Setting up

## Environment Variables

Before run, you will need to add the following environment variables to your `.env` file:

- `GRPC_ENDPOINT` - Your Geyser RPC endpoint url.

- `GRPC_X_TOKEN` - Leave it set to `None` if your Geyser RPC does not require a token for authentication.


- `GRPC_SERVER_ENDPOINT` - The address of its gRPC server. By default is set at `0.0.0.0:50051`.

## Run Command

```
RUSTFLAGS="-C target-cpu=native" RUST_LOG=info cargo run --release --bin shredstream-decoder
```

# Source code

If you are really interested in the source code, please contact me for details and demo on Discord: `.xanr`.

# Solana Sniper Bot

A high-performance Rust-based application that monitors transactions and executes trades with lightning speed on Solana DEXs like PumpFun, PumpSwap, and Raydium.

## Features

- **Lightning-Fast Execution** - Sub-second trade execution with optimized RPC calls
- **Real-time Transaction Monitoring** - Uses Yellowstone gRPC to get transaction data with minimal latency
- **Multi-address Support** - Can monitor multiple wallet addresses simultaneously
- **Protocol Support** - Compatible with PumpFun, PumpSwap, and Raydium DEX platforms
- **Automated Trading** - Executes buy and sell transactions automatically when conditions are met
- **Notification System** - Sends trade alerts and status updates via Telegram
- **Customizable Trading Parameters** - Configurable limits, timing, and amount settings
- **Selling Strategy** - Includes built-in selling strategy options for maximizing profits
- **Whale Detection** - Advanced algorithms to detect and follow large wallet movements
- **MEV Protection** - Built-in protection against Maximal Extractable Value attacks

## Project Structure

The codebase is organized into several modules:

- **engine/** - Core trading logic including sniper bot functionality, selling strategies, transaction parsing, and retry mechanisms
- **dex/** - Protocol-specific implementations for PumpFun, PumpSwap, and Raydium
- **common/** - Shared utilities, configuration, constants, caching, and logging
- **core/** - Core system functionality for tokens and transactions
- **services/** - External service integrations (RPC clients, cache maintenance, Zeroslot)
- **error/** - Error handling and definitions

## Setup

### Environment Variables

To run this bot, you will need to configure the following environment variables:

#### Required Variables

- `GRPC_ENDPOINT` - Your Yellowstone gRPC endpoint URL
- `GRPC_X_TOKEN` - Your Yellowstone authentication token
- `COPY_TRADING_TARGET_ADDRESS` - Wallet address(es) to monitor for trades (comma-separated for multiple addresses)

#### Telegram Notifications

To enable Telegram notifications:

- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `TELEGRAM_CHAT_ID` - Your chat ID for receiving notifications

#### Optional Variables

- `IS_MULTI_COPY_TRADING` - Set to `true` to monitor multiple addresses (default: `false`)
- `PROTOCOL_PREFERENCE` - Preferred protocol to use (`pumpfun`, `pumpswap`, or `auto` for automatic detection)
- `COUNTER_LIMIT` - Maximum number of trades to execute
## Usage

```bash
# Build the project
cargo build --release

# Run the bot
cargo run --release

# Additional commands:
# Wrap SOL to WSOL
cargo run --release -- --wrap

# Unwrap WSOL to SOL
cargo run --release -- --unwrap

# Close all token accounts
cargo run --release -- --close
```

Once started, the sniper bot will:

1. Connect to the Yellowstone gRPC endpoint
2. Monitor transactions from the specified wallet address(es)
3. Automatically execute buy and sell transactions when conditions are met
4. Send notifications via Telegram for detected transactions and executed trades
5. Manage token accounts and WSOL conversions automatically
6. Detect whale movements and large transactions
7. Execute trades with minimal latency for maximum profit potential

## Recent Updates

- Added PumpSwap notification mode (can monitor without executing trades)
- Implemented concurrent transaction processing using tokio tasks
- Enhanced error handling and reporting
- Improved selling strategy implementation
- Added WSOL wrapping/unwrapping utilities
- Implemented token account management and cleanup
- Added cache system for improved performance
- Enhanced transaction retry logic for better reliability
- Streamlined codebase by removing external API dependencies
- Optimized for sniper bot functionality with lightning-fast execution
- Added whale detection algorithms for following large movements
- Implemented MEV protection mechanisms

## Contact

For questions or support, please contact the developer.
