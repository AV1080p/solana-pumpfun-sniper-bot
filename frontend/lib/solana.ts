import { Connection, PublicKey, Transaction, SystemProgram, LAMPORTS_PER_SOL } from '@solana/web3.js'
import { api } from './api'

const JUPITER_API_URL = process.env.NEXT_PUBLIC_JUPITER_API_URL || 'https://quote-api.jup.ag/v6'

interface SwapQuote {
  inputMint: string
  outputMint: string
  inAmount: string
  outAmount: string
  otherAmountThreshold: string
  swapMode: string
  slippageBps: number
  platformFee?: any
  priceImpactPct: string
  routePlan: any[]
}

export async function processSolanaPayment(
  publicKey: string,
  amountSol: number,
  tourId: number,
  sendTransaction: (transaction: Transaction, connection: Connection) => Promise<string>,
  connection: Connection
): Promise<{ success: boolean; error?: string }> {
  try {
    const recipientPublicKey = new PublicKey(process.env.NEXT_PUBLIC_PAYMENT_WALLET || '11111111111111111111111111111111')
    const amountLamports = amountSol * LAMPORTS_PER_SOL

    const transaction = new Transaction().add(
      SystemProgram.transfer({
        fromPubkey: new PublicKey(publicKey),
        toPubkey: recipientPublicKey,
        lamports: amountLamports,
      })
    )

    const signature = await sendTransaction(transaction, connection)
    await connection.confirmTransaction(signature, 'confirmed')

    // Notify backend of successful payment
    await api.post('/payments/solana', {
      tour_id: tourId,
      signature,
      amount: amountSol,
      public_key: publicKey,
    })

    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
}

export async function swapTokens(
  publicKey: string,
  amountSol: number,
  sendTransaction: (transaction: Transaction, connection: Connection) => Promise<string>,
  connection: Connection
): Promise<{ success: boolean; error?: string }> {
  try {
    // USDC mint address (devnet)
    const USDC_MINT = '4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU'
    const SOL_MINT = 'So11111111111111111111111111111111111111112'

    // Get quote from Jupiter
    const quoteResponse = await fetch(
      `${JUPITER_API_URL}/quote?inputMint=${USDC_MINT}&outputMint=${SOL_MINT}&amount=${amountSol * LAMPORTS_PER_SOL}&slippageBps=50`
    )

    if (!quoteResponse.ok) {
      throw new Error('Failed to get swap quote')
    }

    const quote: SwapQuote = await quoteResponse.json()

    // Get swap transaction from Jupiter
    const swapResponse = await fetch(`${JUPITER_API_URL}/swap`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        quoteResponse: quote,
        userPublicKey: publicKey,
        wrapAndUnwrapSol: true,
        dynamicComputeUnitLimit: true,
        prioritizationFeeLamports: 'auto',
      }),
    })

    if (!swapResponse.ok) {
      throw new Error('Failed to get swap transaction')
    }

    const { swapTransaction } = await swapResponse.json()

    // Deserialize and send transaction
    const transaction = Transaction.from(Buffer.from(swapTransaction, 'base64'))
    const signature = await sendTransaction(transaction, connection)
    await connection.confirmTransaction(signature, 'confirmed')

    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
}

