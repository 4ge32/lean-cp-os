import LeanCpOs.Task.Model

namespace Book.TaskControl
open LeanCpOs.TaskControl

-- ID 0 = A、1 = B、2 = H。大きい priority が優先される。
def cfg : Config := [⟨2, 2, true⟩, ⟨2, 1, true⟩, ⟨3, 1, true⟩]

-- 最初の依頼はモデルの ISR 境界で投入する。StartOS ではない。
def boot (c : Config) (id : Nat) : State :=
  (exitISR c (activate c (enterISR initial).state id 1).state).state

def a : State := (stepPc (boot cfg 0) 0).state
def ab : State := (activate cfg a 1 0).state
def aba : State := (activate cfg ab 0 0).state
#guard a.current = some ⟨0, 1⟩
#guard aba.ready = [⟨1, 0⟩, ⟨0, 0⟩]
#guard activeCount aba 0 = 2
#guard (activate cfg aba 0 0).status = .limit
#guard (activate cfg aba 0 0).state = aba

-- H が中断しても、A の pc と、先に届いた B の依頼を失わない。
def h : State := (activate cfg aba 2 0).state
#guard h.current = some ⟨2, 0⟩
#guard h.ready = [⟨0, 1⟩, ⟨1, 0⟩, ⟨0, 0⟩]
def resumed : State := (terminate cfg h 0).state
#guard resumed.current = some ⟨0, 1⟩
#guard (schedule cfg resumed 0).state = resumed

def b : State := (terminate cfg resumed 0).state
def nextA : State := (terminate cfg b 0).state
#guard b.current = some ⟨1, 0⟩
#guard nextA.current = some ⟨0, 0⟩
#eval [a, h, resumed, b, nextA].map (fun s => s.current.map Frame.task)

-- ChainTask の失敗では、現在の継続も待ち行列も保存される。
def rejected : Result := chain cfg resumed 1 0
#guard rejected.status = .limit
#guard rejected.state = resumed
#guard rejected.discard = false

-- 上限 1 の B が自己連鎖する。待っていた A が先、新しい B は pc=0。
def progressedB : State := (stepPc b 0).state
def restarted : Result := chain cfg progressedB 1 0
#guard activeCount progressedB 1 = 1
#guard restarted.status = .ok
#guard restarted.discard = true
#guard restarted.state.current = some ⟨0, 0⟩
#guard restarted.state.ready = [⟨1, 0⟩]

-- 非プリエンプティブな L は、Schedule で初めて H に譲る。
def cooperative : Config := [⟨1, 1, false⟩, ⟨3, 1, true⟩]
def low : State := (stepPc (boot cooperative 0) 0).state
def waiting : State := (activate cooperative low 1 0).state
#guard waiting.current = some ⟨0, 1⟩
#guard waiting.ready = [⟨1, 0⟩]
def yielded : Result := schedule cooperative waiting 0
#guard yielded.status = .ok
#guard yielded.discard = false
#guard yielded.state.current = some ⟨1, 0⟩
#guard (terminate cooperative yielded.state 0).state.current = some ⟨0, 1⟩

-- 演習の解答: 進行していた B を終え、別タスク H を起動する。
def toHigh : Result := chain cfg progressedB 2 0
#guard toHigh.status = .ok
#guard toHigh.discard = true
#guard toHigh.state.current = some ⟨2, 0⟩
#guard activeCount toHigh.state 1 = 0
#guard toHigh.state.ready = [⟨0, 0⟩]

end Book.TaskControl
