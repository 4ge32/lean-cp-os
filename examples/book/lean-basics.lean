import LeanCpOs.Model

open LeanCpOs

namespace Book.LeanBasics

-- 入力の形ごとに、返す文字列を定める。
def label : Task → String
  | .low => "low"
  | .mid => "mid"
  | .high => "high"

-- 操作は新しい状態を返す。initial 自体は書き換わらない。
def activated : State := (activate initial (some .low)).state
def untouched : State := initial

-- State 型の値でも、スケジューラの規則を満たすとは限らない。
def broken : State :=
  { active := ⟨false, false, false⟩, current := some .low }

#eval label .high
#eval priority .high
#eval activated.current
#eval untouched.current
#eval decide (Valid activated)
#eval decide (Valid broken)

#guard label .mid = "mid"
#guard priority .high = 3
#guard activated.current = some .low
#guard untouched.current = none
#guard Valid activated
#guard ¬ Valid broken

-- rfl は定義を展開して一致することを確認する証明。
example : priority .high = 3 := rfl
example (a : Active) : Valid (schedule a) := rfl

end Book.LeanBasics
