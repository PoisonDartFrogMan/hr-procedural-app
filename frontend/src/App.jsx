import React, { useEffect, useMemo, useState } from 'react'
import { askNotificationPermission, fetchJSON, getPublicKey, registerServiceWorker, subscribePush, triggerUpcoming } from './api'

const initialForm = {
  type: '入社',
}

export default function App() {
  const [form, setForm] = useState(initialForm)
  const [employees, setEmployees] = useState([])
  const [selectedEmployee, setSelectedEmployee] = useState(null)
  const [tasks, setTasks] = useState([])
  const [statusMsg, setStatusMsg] = useState('')

  async function refreshEmployees() {
    const data = await fetchJSON('/api/employees')
    setEmployees(data)
  }

  useEffect(() => {
    refreshEmployees()
  }, [])

  useEffect(() => {
    if (!selectedEmployee) return
    fetchJSON(`/api/employees/${selectedEmployee.id}/tasks`).then(setTasks)
  }, [selectedEmployee])

  async function handleSubmit(e) {
    e.preventDefault()
    setStatusMsg('')
    try {
      let url = ''
      const payload = { ...form }
      if (form.type === '入社') url = '/api/employees/onboarding'
      if (form.type === '退社') url = '/api/employees/offboarding'
      if (form.type === '異動') url = '/api/employees/transfer'
      const res = await fetchJSON(url, { method: 'POST', body: JSON.stringify(payload) })
      setStatusMsg('手続きが登録されました')
      await refreshEmployees()
      if (res.employee) setSelectedEmployee(res.employee)
    } catch (err) {
      setStatusMsg(String(err))
    }
  }

  async function handleRegisterPush() {
    const perm = await askNotificationPermission()
    if (perm !== 'granted') {
      alert('通知の許可が必要です')
      return
    }
    const reg = await registerServiceWorker()
    const publicKey = await getPublicKey()
    await subscribePush(reg, publicKey, selectedEmployee?.id || null)
    alert('プッシュ通知を登録しました')
  }

  async function handleNotifyUpcoming() {
    const res = await triggerUpcoming(24)
    alert(`通知対象タスク: ${res.tasks}, 送信件数(試行): ${res.notifications_sent}`)
  }

  const type = form.type
  const fields = useMemo(() => {
    if (type === '入社') return onboardingFields
    if (type === '退社') return offboardingFields
    if (type === '異動') return transferFields
    return []
  }, [type])

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <h1>人事手続きサポート</h1>
      <section>
        <h2>手続きの選択</h2>
        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr' }}>
          <div style={{ gridColumn: '1 / -1' }}>
            <label>
              区分：
              <select value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}>
                <option>入社</option>
                <option>退社</option>
                <option>異動</option>
              </select>
            </label>
          </div>

          {fields.map((f) => (
            <Field key={f.name} field={f} value={form[f.name] || ''} onChange={(v) => setForm({ ...form, [f.name]: v })} />
          ))}

          <div style={{ gridColumn: '1 / -1', marginTop: 12 }}>
            <button type="submit">登録</button>
            {statusMsg && <span style={{ marginLeft: 12 }}>{statusMsg}</span>}
          </div>
        </form>
      </section>

      <hr />

      <section>
        <h2>従業員一覧</h2>
        <ul>
          {employees.map(e => (
            <li key={e.id}>
              <button onClick={() => setSelectedEmployee(e)} style={{ marginRight: 8 }}>表示</button>
              {e.full_name}（{e.status}） / {e.department || '-'} / ID: {e.employee_id}
            </li>
          ))}
        </ul>
      </section>

      {selectedEmployee && (
        <section>
          <h2>スケジュール表: {selectedEmployee.full_name}</h2>
          <div style={{ marginBottom: 8 }}>
            <button onClick={handleRegisterPush}>プッシュ通知を登録</button>
            <button onClick={handleNotifyUpcoming} style={{ marginLeft: 8 }}>24時間以内の期限を通知</button>
          </div>
          <TaskTable tasks={tasks} onStatusChange={async (id, status) => {
            await fetchJSON(`/api/tasks/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) })
            const refreshed = await fetchJSON(`/api/employees/${selectedEmployee.id}/tasks`)
            setTasks(refreshed)
          }} />
        </section>
      )}
    </div>
  )
}

function Field({ field, value, onChange }) {
  const { label, name, type = 'text', placeholder } = field
  return (
    <label style={{ display: 'flex', flexDirection: 'column' }}>
      {label}
      {type === 'checkbox' ? (
        <input type="checkbox" checked={!!value} onChange={e => onChange(e.target.checked)} />
      ) : (
        <input type={type} value={value} placeholder={placeholder}
               onChange={e => onChange(e.target.value)} />
      )}
    </label>
  )
}

function TaskTable({ tasks, onStatusChange }) {
  return (
    <table border="1" cellPadding="6" style={{ borderCollapse: 'collapse', width: '100%' }}>
      <thead>
        <tr>
          <th>タスク名</th>
          <th>期日</th>
          <th>担当者</th>
          <th>進捗</th>
        </tr>
      </thead>
      <tbody>
        {tasks.map(t => (
          <tr key={t.id}>
            <td>{t.name}</td>
            <td>{new Date(t.due_date).toLocaleString()}</td>
            <td>{t.assignee}</td>
            <td>
              <select value={t.status} onChange={e => onStatusChange(t.id, e.target.value)}>
                <option>未完了</option>
                <option>進行中</option>
                <option>完了</option>
              </select>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// Field definitions
const onboardingFields = [
  { label: '氏名', name: 'full_name' },
  { label: 'ふりがな', name: 'furigana' },
  { label: '住所', name: 'address' },
  { label: '連絡先', name: 'phone_number' },
  { label: '入社日', name: 'date_of_joining', type: 'date' },
  { label: '前職の退社日', name: 'previous_job_leaving_date', type: 'date' },
  { label: '給与', name: 'salary' },
  { label: 'グレード', name: 'grade' },
  { label: 'ダブルワークの有無', name: 'is_double_work', type: 'checkbox' },
  { label: '扶養の有無', name: 'is_dependent', type: 'checkbox' },
  { label: '勤務予定部署', name: 'scheduled_department' },
  { label: '勤務予定時間', name: 'scheduled_working_hours' },
  { label: '年齢', name: 'age', type: 'number' },
  { label: '通勤方法', name: 'commute_method' },
  { label: '雇用区分', name: 'employment_type' },
]

const offboardingFields = [
  { label: '社員ID（社内IDまたは自動ID）', name: 'employee_id', placeholder: 'EMP...' },
  { label: '最終出勤日', name: 'last_working_day', type: 'date' },
  { label: '退職日', name: 'date_of_leaving', type: 'date' },
  { label: '退職届の確認', name: 'is_resignation_submitted', type: 'checkbox' },
  { label: '引継ぎ状況', name: 'handover_status' },
  { label: '貸与品の返却', name: 'is_company_property_returned', type: 'checkbox' },
  { label: '退職金の有無', name: 'is_severance_pay', type: 'checkbox' },
]

const transferFields = [
  { label: '社員ID（社内IDまたは自動ID）', name: 'employee_id', placeholder: 'EMP...' },
  { label: '所属部署', name: 'department' },
  { label: '異動先部署', name: 'transfer_destination_department' },
  { label: '異動日', name: 'transfer_date', type: 'date' },
  { label: '勤務時間の変更', name: 'is_working_hours_changed', type: 'checkbox' },
  { label: '通勤方法の変更', name: 'is_commute_method_changed', type: 'checkbox' },
]

