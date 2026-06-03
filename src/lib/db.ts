import Database from 'better-sqlite3'
import path from 'path'
import { Signal, Brand } from './types'

const DB_PATH = path.join(process.cwd(), 'data', 'ooh_signal.db')

let db: Database.Database | null = null

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH, { readonly: true })
  }
  return db
}

export function getSignals(options: {
  limit?: number
  offset?: number
  industry?: string
  signalType?: string
  minScore?: number
  search?: string
} = {}): Signal[] {
  const db = getDb()
  let query = 'SELECT * FROM signals WHERE 1=1'
  const params: any[] = []

  if (options.industry) {
    query += ' AND industry = ?'
    params.push(options.industry)
  }
  if (options.signalType) {
    query += ' AND signal_type = ?'
    params.push(options.signalType)
  }
  if (options.minScore) {
    query += ' AND score >= ?'
    params.push(options.minScore)
  }
  if (options.search) {
    query += ' AND (brand_name LIKE ? OR title LIKE ? OR summary LIKE ?)'
    const term = `%${options.search}%`
    params.push(term, term, term)
  }

  query += ' ORDER BY collected_at DESC LIMIT ? OFFSET ?'
  params.push(options.limit || 50, options.offset || 0)

  return db.prepare(query).all(...params) as Signal[]
}

export function getBrands(options: {
  industry?: string
  limit?: number
} = {}): Brand[] {
  const db = getDb()
  let query = 'SELECT * FROM brands WHERE 1=1'
  const params: any[] = []

  if (options.industry) {
    query += ' AND industry = ?'
    params.push(options.industry)
  }

  query += ' ORDER BY latest_score DESC LIMIT ?'
  params.push(options.limit || 100)

  return db.prepare(query).all(...params) as Brand[]
}
