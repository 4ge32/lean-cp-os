namespace LeanCpOs

/- M0: exactly three static basic tasks. Larger numeric priority wins.
   Pure transition semantics only; no interrupt or machine context semantics. -/
inductive Task where
  | low | mid | high
  deriving DecidableEq, Repr

def priority : Task → Nat
  | .low => 1 | .mid => 2 | .high => 3

structure Active where
  low : Bool
  mid : Bool
  high : Bool
  deriving DecidableEq, Repr

def Active.get (a : Active) : Task → Bool
  | .low => a.low | .mid => a.mid | .high => a.high

def Active.set (a : Active) (t : Task) (b : Bool) : Active :=
  match t with
  | .low => { a with low := b }
  | .mid => { a with mid := b }
  | .high => { a with high := b }

def select (a : Active) : Option Task :=
  if a.high then some .high else if a.mid then some .mid
  else if a.low then some .low else none

structure State where
  active : Active
  current : Option Task
  deriving DecidableEq, Repr

def Valid (s : State) : Prop := s.current = select s.active
instance (s : State) : Decidable (Valid s) := inferInstanceAs (Decidable (_ = _))

def schedule (a : Active) : State := ⟨a, select a⟩
def initial : State := schedule ⟨false, false, false⟩

inductive TaskState where
  | suspended | ready | running
  deriving DecidableEq, Repr

def taskState (s : State) (t : Task) : TaskState :=
  if s.active.get t then
    if s.current = some t then .running else .ready
  else .suspended

inductive Status where
  | ok | id | limit | callevel | badInput
  deriving DecidableEq, Repr

/- Return means the service's logical response; an ActivateTask preemption may
   defer delivery to its caller. Dispatch means the terminated continuation
   MUST be discarded. This is not itself a context-switch implementation. -/
inductive Control where
  | returned (status : Status)
  | dispatch (next : Option Task)
  deriving DecidableEq, Repr

structure Result where
  state : State
  control : Control
  deriving DecidableEq, Repr

def activate (s : State) (target : Option Task) : Result :=
  match target with
  | none => ⟨s, .returned .id⟩
  | some t =>
    if s.active.get t then ⟨s, .returned .limit⟩
    else ⟨schedule (s.active.set t true), .returned .ok⟩

def terminate (s : State) : Result :=
  match s.current with
  | none => ⟨s, .returned .callevel⟩ -- project-level idle rejection
  | some t =>
    let next := schedule (s.active.set t false)
    ⟨next, .dispatch next.current⟩

def getTaskID (s : State) : Status × Option Task := (.ok, s.current)
def getTaskState (s : State) (target : Option Task) : Status × Option TaskState :=
  match target with
  | none => (.id, none)
  | some t => (.ok, some (taskState s t))

end LeanCpOs
