#!/usr/bin/env node
// Generates dashboard/src/data/changelog.json from `git log` at repo root.
// Runs automatically before dev (`predev`) and build (`prebuild`).
// Output: array of { sha, date, type, scope, sprint, subject } sorted newest-first.
//
// Defensive against non-conventional commits:
//   - "feat(S140): subject" → { type: 'feat', scope: 'S140', sprint: 'S140', subject }
//   - "fix: subject"        → { type: 'fix', scope: null, sprint: null, subject }
//   - "Sprint 56 hotfix: …" → { type: 'other', scope: null, sprint: 'S56', subject }
//   - anything else         → { type: 'other', scope: null, sprint: null, subject: <raw> }

import { execSync } from 'node:child_process'
import { writeFileSync, mkdirSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const REPO_ROOT = resolve(__dirname, '..', '..')   // dashboard/scripts/ → dashboard/ → repo root
const OUTPUT_DIR = resolve(__dirname, '..', 'src', 'data')
const OUTPUT_PATH = resolve(OUTPUT_DIR, 'changelog.json')

// Use a separator unlikely to appear in subjects. \x1f = ASCII unit-separator.
const SEP = '\x1f'
const LOG_CMD = `git log --no-merges --pretty=format:"%H${SEP}%aI${SEP}%s"`

let raw
try {
  raw = execSync(LOG_CMD, { cwd: REPO_ROOT, encoding: 'utf8', maxBuffer: 50 * 1024 * 1024 })
} catch (err) {
  console.error('generate-changelog: git log failed:', err.message)
  console.error('  Are you running outside a git repo? Falling back to empty changelog.')
  mkdirSync(OUTPUT_DIR, { recursive: true })
  writeFileSync(OUTPUT_PATH, '[]\n')
  process.exit(0)
}

const CONVENTIONAL_RE = /^(feat|fix|chore|docs|refactor|test|style|perf|build|ci)(?:\(([^)]+)\))?:\s*(.+)$/
const SPRINT_SCOPE_RE = /^S(\d+)([a-z]?)$/i
const SPRINT_IN_SUBJECT_RE = /\bS(?:print)?\s*(\d+)([a-z]?)\b/i

const commits = raw
  .split('\n')
  .filter(Boolean)
  .map((line) => {
    const [sha, date, ...subjectParts] = line.split(SEP)
    const subject = subjectParts.join(SEP).trim()
    const shortSha = sha.slice(0, 7)

    const conv = subject.match(CONVENTIONAL_RE)
    if (conv) {
      const [, type, rawScope, message] = conv
      const scope = rawScope || null
      // Extract sprint from scope if present (S140, S140a, etc.)
      let sprint = null
      if (scope) {
        const sm = scope.match(SPRINT_SCOPE_RE)
        if (sm) sprint = 'S' + sm[1] + (sm[2] || '')
      }
      // Fallback: sprint mentioned in subject text
      if (!sprint) {
        const sm2 = message.match(SPRINT_IN_SUBJECT_RE)
        if (sm2) sprint = 'S' + sm2[1] + (sm2[2] || '')
      }
      return { sha: shortSha, date, type, scope, sprint, subject: message }
    }

    // Non-conventional: look for "Sprint NN" pattern in subject
    const sm = subject.match(SPRINT_IN_SUBJECT_RE)
    const sprint = sm ? 'S' + sm[1] + (sm[2] || '') : null
    return { sha: shortSha, date, type: 'other', scope: null, sprint, subject }
  })

mkdirSync(OUTPUT_DIR, { recursive: true })
writeFileSync(OUTPUT_PATH, JSON.stringify(commits, null, 2) + '\n')

const counts = commits.reduce((acc, c) => {
  acc[c.type] = (acc[c.type] || 0) + 1
  return acc
}, {})
console.log(`generate-changelog: wrote ${commits.length} commits → ${OUTPUT_PATH}`)
console.log(`  Distribution: ${Object.entries(counts).map(([k, v]) => `${k}=${v}`).join(' · ')}`)
