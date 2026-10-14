import LeanCpOs.Task.Model

namespace LeanCpOs.TaskControl

local instance lawfulNatBEq : LawfulBEq Nat where
  eq_of_beq := fun h => of_decide_eq_true h
  rfl := decide_eq_true rfl

/- Service-level contracts complement the configuration and queue invariants.
   These quantify over arbitrary states/configurations: error atomicity does
   not rely on a small enumeration of task identifiers. -/
theorem activate_error_unchanged (cfg : Config) (s : State) (target ctx : Nat)
    (h : (activate cfg s target ctx).status ≠ .ok) :
    (activate cfg s target ctx).state = s := by
  cases he : cfg[target]? <;> simp only [activate, he] at *
  all_goals repeat' split
  all_goals simp_all [fail]

theorem terminate_error_unchanged (cfg : Config) (s : State) (ctx : Nat)
    (h : (terminate cfg s ctx).status ≠ .ok) :
    (terminate cfg s ctx).state = s := by
  unfold terminate at *
  split <;> simp_all [fail]
  split <;> simp_all [fail]

theorem chain_error_unchanged (cfg : Config) (s : State) (target ctx : Nat)
    (h : (chain cfg s target ctx).status ≠ .ok) :
    (chain cfg s target ctx).state = s := by
  cases he : cfg[target]? <;> simp only [chain, he] at *
  all_goals repeat' split
  all_goals simp_all [fail]

theorem schedule_error_unchanged (cfg : Config) (s : State) (ctx : Nat)
    (h : (schedule cfg s ctx).status ≠ .ok) :
    (schedule cfg s ctx).state = s := by
  unfold schedule at *
  split <;> simp_all [fail]
  split <;> simp_all [fail]

theorem getTaskID_unchanged (s : State) (ctx : Nat) :
    (getTaskID s ctx).state = s := by
  simp only [getTaskID]
  split <;> rfl

theorem getTaskState_unchanged (cfg : Config) (s : State) (target ctx : Nat) :
    (getTaskState cfg s target ctx).state = s := by
  simp only [getTaskState]
  split
  · rfl
  · split <;> rfl

theorem terminate_success_discards (cfg : Config) (s : State) (ctx : Nat)
    (h : (terminate cfg s ctx).status = .ok) :
    (terminate cfg s ctx).discard = true := by
  unfold terminate at *
  split <;> simp_all [fail]
  split <;> simp_all [fail]

theorem chain_success_discards (cfg : Config) (s : State) (target ctx : Nat)
    (h : (chain cfg s target ctx).status = .ok) :
    (chain cfg s target ctx).discard = true := by
  cases he : cfg[target]? <;> simp only [chain, he] at *
  all_goals repeat' split
  all_goals simp_all [fail]

theorem mayPreempt_deferred_in_ISR (cfg : Config) (s : State) (explicit : Bool)
    (h : s.isrDepth ≠ 0) : mayPreempt cfg s explicit = s := by
  simp [mayPreempt, h]

theorem mayPreempt_keeps_equal_or_lower (cfg : Config) (s : State)
    (running next : Frame) (rest : List Frame) (explicit : Bool)
    (hc : s.current = some running) (hq : choose cfg s.ready = some (next, rest))
    (hp : priority cfg next ≤ priority cfg running) :
    mayPreempt cfg s explicit = s := by
  simp only [mayPreempt]
  split
  · rfl
  · simp only [hc]
    split
    · simp [hq, Nat.not_lt_of_ge hp]
    · rfl

theorem preemption_preserves_continuation (cfg : Config) (s : State)
    (running next : Frame) (rest : List Frame)
    (hc : s.current = some running) (hq : choose cfg s.ready = some (next, rest))
    (hi : s.isrDepth = 0) (hp : priority cfg running < priority cfg next) :
    mayPreempt cfg s true = { s with current := some next, ready := running :: rest } := by
  simp [mayPreempt, hc, hq, hi, hp]

theorem higher_priority_is_different_task (cfg : Config) (running next : Frame)
    (hp : priority cfg running < priority cfg next) : next.task ≠ running.task := by
  intro he
  simp [priority, he] at hp

theorem nonpreemptive_keeps_current (cfg : Config) (s : State) (f : Frame)
    (tc : TaskConfig) (hc : s.current = some f) (ht : cfg[f.task]? = some tc)
    (hn : tc.preemptive = false) : mayPreempt cfg s false = s := by
  simp only [mayPreempt]
  split
  · rfl
  · simp [hc, ht, hn]

theorem activate_success_in_ISR_queued (cfg : Config) (s : State) (target ctx : Nat)
    (hi : s.isrDepth ≠ 0) (h : (activate cfg s target ctx).status = .ok) :
    (activate cfg s target ctx).state = { s with ready := s.ready ++ [⟨target, 0⟩] } := by
  cases he : cfg[target]? <;> simp only [activate, he] at *
  all_goals repeat' split
  all_goals simp_all [fail]
  exact mayPreempt_deferred_in_ISR cfg _ false hi

theorem self_chain_restarts_at_limit (cfg : Config) (s : State)
    (running : Frame) (tc : TaskConfig) (ctx : Nat)
    (hc : s.current = some running) (ht : cfg[running.task]? = some tc)
    (ha : taskAllowed s ctx = true) (hr : ctx / 4 ≠ 1) :
    chain cfg s running.task ctx =
      ⟨dispatch cfg { s with current := none, ready := s.ready ++ [⟨running.task, 0⟩] }, .ok, true, 0⟩ := by
  simp [chain, hc, ht, ha, hr]

theorem terminate_resource_guard (cfg : Config) (s : State) (ctx : Nat)
    (ha : taskAllowed s ctx = true) (hr : ctx / 4 = 1) :
    terminate cfg s ctx = fail s .resource := by
  simp [terminate, ha, hr]

theorem chain_resource_guard (cfg : Config) (s : State) (target ctx : Nat)
    (ha : taskAllowed s ctx = true) (hr : ctx / 4 = 1) :
    chain cfg s target ctx = fail s .resource := by
  simp [chain, ha, hr]

theorem schedule_resource_guard (cfg : Config) (s : State) (ctx : Nat)
    (ha : taskAllowed s ctx = true) (hr : ctx / 4 = 1) :
    schedule cfg s ctx = fail s .resource := by
  simp [schedule, ha, hr]

end LeanCpOs.TaskControl
