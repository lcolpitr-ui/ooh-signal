import { NextRequest, NextResponse } from 'next/server'
import * as XLSX from 'xlsx'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return NextResponse.json({ error: '请上传文件' }, { status: 400 })
    }

    // 检查文件大小 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      return NextResponse.json({ error: '文件太大，请上传小于10MB的文件' }, { status: 400 })
    }

    const buffer = await file.arrayBuffer()
    let data: Record<string, unknown>[] = []

    try {
      data = parseFile(buffer, file.name)
    } catch (parseError) {
      console.error('Parse error:', parseError)
      return NextResponse.json({ error: '文件格式错误，请检查文件内容' }, { status: 400 })
    }

    if (!data || data.length === 0) {
      return NextResponse.json({ error: '无法解析文件内容，请确保文件包含表格数据' }, { status: 400 })
    }

    return NextResponse.json({
      success: true,
      filename: file.name,
      rows: data.length,
      data,
      columns: Object.keys(data[0] || {}),
    })
  } catch (error) {
    console.error('Upload error:', error)
    return NextResponse.json({ error: '文件处理失败，请重试' }, { status: 500 })
  }
}

function parseFile(buffer: ArrayBuffer, filename: string): Record<string, unknown>[] {
  const ext = filename.toLowerCase().split('.').pop()

  // Excel 文件
  if (ext === 'xlsx' || ext === 'xls') {
    const workbook = XLSX.read(buffer, { type: 'array' })
    const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
    return XLSX.utils.sheet_to_json(firstSheet)
  }

  // CSV 文件
  if (ext === 'csv') {
    const text = new TextDecoder().decode(buffer)
    return parseCSV(text)
  }

  // 文本文件
  if (ext === 'txt' || ext === 'text') {
    const text = new TextDecoder().decode(buffer)
    return parseTextFile(text)
  }

  // Word 文件 (简单提取)
  if (ext === 'docx' || ext === 'doc') {
    const text = new TextDecoder().decode(buffer)
    return parseTextFile(text)
  }

  // PDF (简单提取文本)
  if (ext === 'pdf') {
    const text = new TextDecoder().decode(buffer)
    return parseTextFile(text)
  }

  return []
}

function parseCSV(text: string): Record<string, unknown>[] {
  const lines = text.split('\n').filter(line => line.trim())
  if (lines.length < 2) return []

  const headers = parseCSVLine(lines[0])
  const rows: Record<string, unknown>[] = []

  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i])
    const row: Record<string, unknown> = {}
    headers.forEach((header, index) => {
      row[header] = values[index] || ''
    })
    rows.push(row)
  }

  return rows
}

function parseCSVLine(line: string): string[] {
  const result: string[] = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    if (char === '"') {
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  result.push(current.trim())
  return result
}

function parseTextFile(text: string): Record<string, unknown>[] {
  // 尝试识别表格格式的文本
  const lines = text.split('\n').filter(line => line.trim())

  // 检查是否是表格格式（用制表符或多个空格分隔）
  const separator = detectSeparator(lines)
  if (separator && lines.length >= 2) {
    const headers = lines[0].split(separator).map(h => h.trim()).filter(Boolean)
    const rows: Record<string, unknown>[] = []

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(separator).map(v => v.trim())
      const row: Record<string, unknown> = {}
      headers.forEach((header, index) => {
        row[header] = values[index] || ''
      })
      rows.push(row)
    }

    return rows
  }

  // 如果不是表格格式，尝试解析为资源列表
  return parseResourceList(lines)
}

function detectSeparator(lines: string[]): string | RegExp | null {
  if (lines.length < 2) return null

  const firstLine = lines[0]
  const tabCount = (firstLine.match(/\t/g) || []).length
  const multiSpaceCount = (firstLine.match(/\s{2,}/g) || []).length

  if (tabCount >= 2) return '\t'
  if (multiSpaceCount >= 2) return /\s{2,}/
  if (firstLine.includes('|') && firstLine.split('|').length >= 3) return '|'

  return null
}

function parseResourceList(lines: string[]): Record<string, unknown>[] {
  const resources: Record<string, unknown>[] = []

  // 尝试识别每个资源块
  let currentResource: Record<string, unknown> = {}

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue

    // 检查是否是新资源的开始（数字开头或特定标记）
    if (/^\d+[.、]/.test(trimmed) || /^[【\[]/.test(trimmed)) {
      if (Object.keys(currentResource).length > 0) {
        resources.push(currentResource)
      }
      currentResource = { name: trimmed.replace(/^\d+[.、]\s*/, '').replace(/[【\]】]/g, '') }
      continue
    }

    // 尝试解析键值对
    const kvMatch = trimmed.match(/^([^：:]+)[：:](.+)$/)
    if (kvMatch) {
      const key = kvMatch[1].trim()
      const value = kvMatch[2].trim()
      currentResource[key] = value
    } else if (currentResource.name) {
      // 附加到描述
      currentResource.description = (currentResource.description || '') + trimmed
    }
  }

  if (Object.keys(currentResource).length > 0) {
    resources.push(currentResource)
  }

  return resources
}
