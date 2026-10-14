import LeanCpOs.Model

open LeanCpOs

namespace Book.FirstRun

-- 各名前は「操作を終えた後の状態」を表す。
def s1 : State := (activate initial (some .low)).state
def s2 : State := (activate s1 (some .high)).state
def s3 : State := (terminate s2).state

-- #eval は計算した値を表示する。
#eval s1.current
#eval s2.current
#eval taskState s2 .low
#eval s3.current
#eval (activate s2 (some .high)).control

-- #guard は期待と違う結果になったときにエラーを出す。
#guard initial.current = none
#guard s1.current = some .low
#guard s2.current = some .high
#guard taskState s2 .low = .ready
#guard s3.current = some .low
#guard (activate s2 (some .high)).control = .returned .limit
#guard (activate s2 (some .high)).state = s2
#guard (terminate initial).control = .returned .callevel
#guard Valid s3

end Book.FirstRun
