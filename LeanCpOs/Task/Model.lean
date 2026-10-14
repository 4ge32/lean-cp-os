namespace LeanCpOs.TaskControl

/- Single-core basic-task transition model. Larger numeric priorities win.
   Each queued frame is one activation, including pending repeated requests.
   The first highest-priority frame wins; interrupted frames return to the
   front, ahead of equal-priority activations. pc is observable model progress,
   not a machine program counter. Interrupt nesting is an environment boundary.
   Resources are caller guards; a resource subsystem is outside this model. -/
structure TaskConfig where
  priority : Nat
  maxActivations : Nat
  preemptive : Bool
  deriving DecidableEq, Repr

abbrev Config := List TaskConfig

structure Frame where
  task : Nat
  pc : Nat := 0
  deriving DecidableEq, Repr

structure State where
  current : Option Frame := none
  ready : List Frame := []
  isrDepth : Nat := 0
  deriving DecidableEq, Repr

def initial : State := {}

def priority (cfg : Config) (f : Frame) : Nat :=
  ((cfg[f.task]?).map TaskConfig.priority).getD 0

/- Extract exactly one frame, retaining FIFO order among the others. -/
def choose (cfg : Config) : List Frame → Option (Frame × List Frame)
  | [] => none
  | f :: fs =>
    match choose cfg fs with
    | none => some (f, [])
    | some (best, rest) =>
      if priority cfg f ≥ priority cfg best then some (f, fs)
      else some (best, f :: rest)

def dispatch (cfg : Config) (s : State) : State :=
  match choose cfg s.ready with
  | none => { s with current := none }
  | some (f, rest) => { s with current := some f, ready := rest }

def mayPreempt (cfg : Config) (s : State) (explicit : Bool := false) : State :=
  if s.isrDepth != 0 then s else
  match s.current with
  | none => dispatch cfg s
  | some running =>
    let preemptive := ((cfg[running.task]?).map TaskConfig.preemptive).getD false
    if explicit || preemptive then
      match choose cfg s.ready with
      | none => s
      | some (next, rest) =>
        if priority cfg next > priority cfg running then
          { s with current := some next, ready := running :: rest }
        else s
    else s

def activeCount (s : State) (t : Nat) : Nat :=
  (s.current.toList ++ s.ready).countP (fun f => f.task == t)

def validConfig (cfg : Config) : Prop :=
  cfg ≠ [] ∧ ∀ tc ∈ cfg, 0 < tc.maxActivations

def Valid (cfg : Config) (s : State) : Prop :=
  (∀ f ∈ s.current.toList ++ s.ready, f.task < cfg.length) ∧
  (∀ t (tc : TaskConfig), cfg[t]? = some tc → activeCount s t ≤ tc.maxActivations)

inductive Status where
  | ok | id | limit | callevel | resource | badInput
  deriving DecidableEq, Repr

structure Result where
  state : State
  status : Status := .ok
  /- True means the calling continuation must be discarded. -/
  discard : Bool := false
  value : Nat := 0
  deriving DecidableEq, Repr

def fail (s : State) (status : Status) : Result := ⟨s, status, false, 0⟩

/- Context 0 is task, 1 is category-2 ISR; other contexts are unsupported.
   Adding 4 records held resources in the environment, solely for the
   TerminateTask/ChainTask/Schedule extended-status guard. -/
def contextAllowed (s : State) (ctx : Nat) (isrAllowed : Bool) : Bool :=
  if ctx ≥ 8 then false else
  match ctx % 4 with
  | 0 => s.isrDepth == 0
  | 1 => isrAllowed && s.isrDepth > 0
  | _ => false

def taskAllowed (s : State) (ctx : Nat) : Bool :=
  contextAllowed s ctx false && s.current.isSome

def activate (cfg : Config) (s : State) (target ctx : Nat) : Result :=
  if !contextAllowed s ctx true || (ctx % 4 == 0 && s.current.isNone) then
    fail s .callevel
  else match cfg[target]? with
  | none => fail s .id
  | some tc =>
    if activeCount s target ≥ tc.maxActivations then fail s .limit
    else { state := mayPreempt cfg { s with ready := s.ready ++ [⟨target, 0⟩] } }

def terminate (cfg : Config) (s : State) (ctx : Nat) : Result :=
  if !taskAllowed s ctx then fail s .callevel
  else if ctx / 4 == 1 then fail s .resource
  else ⟨dispatch cfg { s with current := none }, .ok, true, 0⟩

def chain (cfg : Config) (s : State) (target ctx : Nat) : Result :=
  if !taskAllowed s ctx then fail s .callevel
  else if ctx / 4 == 1 then fail s .resource
  else match cfg[target]? with
  | none => fail s .id
  | some tc =>
    let self := s.current.any (fun f => f.task == target)
    if !self && activeCount s target ≥ tc.maxActivations then fail s .limit
    else ⟨dispatch cfg { s with current := none, ready := s.ready ++ [⟨target, 0⟩] },
      .ok, true, 0⟩

def schedule (cfg : Config) (s : State) (ctx : Nat) : Result :=
  if !taskAllowed s ctx then fail s .callevel
  else if ctx / 4 == 1 then fail s .resource
  else { state := mayPreempt cfg s true }

def getTaskID (s : State) (ctx : Nat) : Result :=
  if !contextAllowed s ctx true then fail s .callevel
  else ⟨s, .ok, false, (s.current.map (fun f => f.task + 1)).getD 0⟩

def taskState (s : State) (target : Nat) : Nat :=
  if s.current.any (fun f => f.task == target) then 3
  else if s.ready.any (fun f => f.task == target) then 2 else 1

def getTaskState (cfg : Config) (s : State) (target ctx : Nat) : Result :=
  if !contextAllowed s ctx true then fail s .callevel
  else if target < cfg.length then ⟨s, .ok, false, taskState s target⟩
  else fail s .id

/- Synthetic progress and ISR boundary commands let executable tests observe
   suspension and deferral without conflating them with OSEK services. -/
def stepPc (s : State) (ctx : Nat) : Result :=
  if !taskAllowed s ctx then fail s .callevel
  else { state := { s with current := s.current.map (fun f => { f with pc := f.pc + 1 }) } }

def enterISR (s : State) : Result := { state := { s with isrDepth := s.isrDepth + 1 } }

def exitISR (cfg : Config) (s : State) : Result :=
  if s.isrDepth == 0 then fail s .callevel
  else { state := mayPreempt cfg { s with isrDepth := s.isrDepth - 1 } }

def step (cfg : Config) (s : State) (op target ctx : Nat) : Result :=
  match op with
  | 0 => activate cfg s target ctx
  | 1 => terminate cfg s ctx
  | 2 => chain cfg s target ctx
  | 3 => schedule cfg s ctx
  | 4 => getTaskID s ctx
  | 5 => getTaskState cfg s target ctx
  | 6 => stepPc s ctx
  | 7 => enterISR s
  | 8 => exitISR cfg s
  | _ => fail s .badInput

end LeanCpOs.TaskControl
