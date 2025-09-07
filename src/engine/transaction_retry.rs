use std::sync::Arc;
use std::time::{Duration, Instant};
use anyhow::{anyhow, Result};
use anchor_client::solana_sdk::{
    pubkey::Pubkey, 
    signature::{Signature, Keypair}, 
    instruction::Instruction,
    transaction::{VersionedTransaction, Transaction},
    signer::Signer,
    hash::Hash,
};
use spl_associated_token_account::get_associated_token_address;
use colored::Colorize;
use tokio::time::sleep;
use base64;

use crate::common::{
    config::{AppState, SwapConfig},
    logger::Logger,
};
use crate::engine::swap::SwapDirection;
use crate::engine::transaction_parser::TradeInfoFromToken;
use crate::core::tx;

/// Maximum number of retry attempts for selling transactions
const MAX_RETRIES: u32 = 3;

/// Delay between retry attempts
const RETRY_DELAY: Duration = Duration::from_secs(2);

/// Timeout for transaction verification
const VERIFICATION_TIMEOUT: Duration = Duration::from_secs(30);

/// Result of a selling transaction attempt
#[derive(Debug)]
pub struct SellTransactionResult {
    pub success: bool,
    pub signature: Option<Signature>,
    pub error: Option<String>,
    pub used_jupiter_fallback: bool,
    pub attempt_count: u32,
}

/// Enhanced transaction verification with retry logic
pub async fn verify_transaction_with_retry(
    signature: &Signature,
    app_state: Arc<AppState>,
    logger: &Logger,
    max_retries: u32,
) -> Result<bool> {
    let start_time = Instant::now();
    
    for attempt in 1..=max_retries {
        if start_time.elapsed() > VERIFICATION_TIMEOUT {
            logger.log(format!("Transaction verification timeout after {:?}", start_time.elapsed()).yellow().to_string());
            return Ok(false);
        }

        logger.log(format!("Verifying transaction attempt {}/{}: {}", attempt, max_retries, signature));

        match app_state.rpc_nonblocking_client.get_signature_statuses(&[*signature]).await {
            Ok(result) => {
                if let Some(status_opt) = result.value.get(0) {
                    if let Some(status) = status_opt {
                        if status.err.is_none() {
                            logger.log(format!("✅ Transaction verified successfully: {}", signature).green().to_string());
                            return Ok(true);
                        } else {
                            logger.log(format!("❌ Transaction failed with error: {:?}", status.err).red().to_string());
                            return Ok(false);
                        }
                    }
                }
            }
            Err(e) => {
                logger.log(format!("RPC error during verification attempt {}: {}", attempt, e).yellow().to_string());
            }
        }

        if attempt < max_retries {
            sleep(Duration::from_millis(1000)).await;
        }
    }

    logger.log(format!("Transaction verification failed after {} attempts", max_retries).red().to_string());
    Ok(false)
}

/// Execute a selling transaction with retry and Jupiter fallback
pub async fn execute_sell_with_retry_and_fallback(
    trade_info: &TradeInfoFromToken,
    sell_config: SwapConfig,
    app_state: Arc<AppState>,
    logger: &Logger,
) -> Result<SellTransactionResult> {
    let token_mint = &trade_info.mint;
    logger.log(format!("🔄 Starting sell transaction with retry for token: {}", token_mint).cyan().to_string());

    // First, try the normal selling flow with retries
    match execute_normal_sell_with_retry(trade_info, sell_config.clone(), app_state.clone(), logger).await {
        Ok(result) => {
            if result.success {
                logger.log(format!("✅ Normal sell succeeded on attempt {}", result.attempt_count).green().to_string());
                return Ok(result);
            }
        }
        Err(e) => {
            logger.log(format!("❌ Normal sell attempts failed: {}", e).yellow().to_string());
        }
    }

    // All sell methods failed
    logger.log(format!("❌ All sell methods failed for token: {}", token_mint).red().to_string());
    Ok(SellTransactionResult {
        success: false,
        signature: None,
        error: Some(format!("All sell methods failed for token: {}", token_mint)),
        used_jupiter_fallback: false,
        attempt_count: MAX_RETRIES,
    })
}

/// Execute normal selling flow with retry logic
async fn execute_normal_sell_with_retry(
    trade_info: &TradeInfoFromToken,
    sell_config: SwapConfig,
    app_state: Arc<AppState>,
    logger: &Logger,
) -> Result<SellTransactionResult> {
    let mut last_error = String::new();

    for attempt in 1..=MAX_RETRIES {
        logger.log(format!("🔄 Normal sell attempt {}/{} for token: {}", attempt, MAX_RETRIES, trade_info.mint).cyan().to_string());

        match execute_single_sell_attempt(trade_info, sell_config.clone(), app_state.clone(), logger).await {
            Ok(signature) => {
                // Verify the transaction
                match verify_transaction_with_retry(&signature, app_state.clone(), logger, 5).await {
                    Ok(verified) => {
                        if verified {
                            logger.log(format!("✅ Normal sell succeeded on attempt {}: {}", attempt, signature).green().to_string());
                            return Ok(SellTransactionResult {
                                success: true,
                                signature: Some(signature),
                                error: None,
                                used_jupiter_fallback: false,
                                attempt_count: attempt,
                            });
                        } else {
                            last_error = format!("Transaction verification failed for signature: {}", signature);
                            logger.log(format!("❌ Attempt {} failed: {}", attempt, last_error).yellow().to_string());
                        }
                    }
                    Err(e) => {
                        last_error = format!("Verification error: {}", e);
                        logger.log(format!("❌ Attempt {} failed: {}", attempt, last_error).yellow().to_string());
                    }
                }
            }
            Err(e) => {
                last_error = e.to_string();
                logger.log(format!("❌ Attempt {} failed: {}", attempt, last_error).yellow().to_string());
            }
        }

        if attempt < MAX_RETRIES {
            logger.log(format!("⏳ Waiting {:?} before retry...", RETRY_DELAY).yellow().to_string());
            sleep(RETRY_DELAY).await;
        }
    }

    Err(anyhow!("Normal sell failed after {} attempts. Last error: {}", MAX_RETRIES, last_error))
}

/// Execute a single sell attempt using the existing selling logic
async fn execute_single_sell_attempt(
    trade_info: &TradeInfoFromToken,
    sell_config: SwapConfig,
    app_state: Arc<AppState>,
    logger: &Logger,
) -> Result<Signature> {
    // Determine which DEX to use based on trade info
    match trade_info.dex_type {
        crate::engine::transaction_parser::DexType::PumpFun => {
            execute_pumpfun_sell_attempt(trade_info, sell_config, app_state, logger).await
        }
        crate::engine::transaction_parser::DexType::PumpSwap => {
            execute_pumpswap_sell_attempt(trade_info, sell_config, app_state, logger).await
        }
        crate::engine::transaction_parser::DexType::RaydiumLaunchpad => {
            execute_raydium_sell_attempt(trade_info, sell_config, app_state, logger).await
        }
        _ => {
            // Default to PumpFun for unknown protocols
            execute_pumpfun_sell_attempt(trade_info, sell_config, app_state, logger).await
        }
    }
}

/// Execute PumpFun sell attempt
async fn execute_pumpfun_sell_attempt(
    trade_info: &TradeInfoFromToken,
    sell_config: SwapConfig,
    app_state: Arc<AppState>,
    logger: &Logger,
) -> Result<Signature> {
    let pump = crate::dex::pump_fun::Pump::new(
        app_state.rpc_nonblocking_client.clone(),
        app_state.rpc_client.clone(),
        app_state.wallet.clone(),
    );

    let (keypair, instructions, _price) = pump.build_swap_from_parsed_data(trade_info, sell_config).await
        .map_err(|e| anyhow!("Failed to build PumpFun swap: {}", e))?;

    let recent_blockhash = app_state.rpc_client.get_latest_blockhash()
        .map_err(|e| anyhow!("Failed to get recent blockhash: {}", e))?;

    let signatures = crate::core::tx::new_signed_and_send_with_landing_mode(
        crate::common::config::TransactionLandingMode::Normal,
        &app_state,
        recent_blockhash,
        &keypair,
        instructions,
        logger,
    ).await.map_err(|e| anyhow!("Failed to send transaction: {}", e))?;

    if signatures.is_empty() {
        return Err(anyhow!("No transaction signature returned"));
    }

    // Parse the string signature to Signature type
    let signature = signatures[0].parse::<Signature>()
        .map_err(|e| anyhow!("Failed to parse signature: {}", e))?;
    Ok(signature)
}

/// Execute Raydium sell attempt
async fn execute_raydium_sell_attempt(
    trade_info: &TradeInfoFromToken,
    sell_config: SwapConfig,
    app_state: Arc<AppState>,
    logger: &Logger,
) -> Result<Signature> {
    let raydium = crate::dex::raydium_launchpad::Raydium::new(
        app_state.wallet.clone(),
        Some(app_state.rpc_client.clone()),
        Some(app_state.rpc_nonblocking_client.clone()),
    );

    let (keypair, instructions, _price) = raydium.build_swap_from_parsed_data(trade_info, sell_config).await
        .map_err(|e| anyhow!("Failed to build Raydium swap: {}", e))?;

    let recent_blockhash = app_state.rpc_client.get_latest_blockhash()
        .map_err(|e| anyhow!("Failed to get recent blockhash: {}", e))?;

    let signatures = crate::core::tx::new_signed_and_send_zeroslot(
        app_state.zeroslot_rpc_client.clone(),
        recent_blockhash,
        &keypair,
        instructions,
        logger,
    ).await.map_err(|e| anyhow!("Failed to send transaction: {}", e))?;

    if signatures.is_empty() {
        return Err(anyhow!("No transaction signature returned"));
    }

    // Parse the string signature to Signature type
    let signature = signatures[0].parse::<Signature>()
        .map_err(|e| anyhow!("Failed to parse signature: {}", e))?;
    Ok(signature)
}

/// Execute PumpSwap sell attempt
async fn execute_pumpswap_sell_attempt(
    trade_info: &TradeInfoFromToken,
    sell_config: SwapConfig,
    app_state: Arc<AppState>,
    logger: &Logger,
) -> Result<Signature> {
    let pump_swap = crate::dex::pump_swap::PumpSwap::new(
        app_state.wallet.clone(),
        Some(app_state.rpc_client.clone()),
        Some(app_state.rpc_nonblocking_client.clone()),
    );

    let (keypair, instructions, _price) = pump_swap.build_swap_from_parsed_data(trade_info, sell_config).await
        .map_err(|e| anyhow!("Failed to build PumpSwap swap: {}", e))?;

    let recent_blockhash = app_state.rpc_client.get_latest_blockhash()
        .map_err(|e| anyhow!("Failed to get recent blockhash: {}", e))?;

    let signatures = crate::core::tx::new_signed_and_send_with_landing_mode(
        crate::common::config::TransactionLandingMode::Normal,
        &app_state,
        recent_blockhash,
        &keypair,
        instructions,
        logger,
    ).await.map_err(|e| anyhow!("Failed to send transaction: {}", e))?;

    if signatures.is_empty() {
        return Err(anyhow!("No transaction signature returned"));
    }

    let signature = signatures[0].parse::<Signature>()
        .map_err(|e| anyhow!("Failed to parse signature: {}", e))?;
    Ok(signature)
}
