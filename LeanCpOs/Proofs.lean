import LeanCpOs.Model

namespace LeanCpOs
set_option maxRecDepth 4096
set_option maxHeartbeats 2000000

theorem initial_valid : Valid initial := rfl
theorem schedule_valid (a : Active) : Valid (schedule a) := rfl

theorem select_member (a : Active) (t : Task) :
    select a = some t → a.get t = true := by
  rcases a with ⟨l, m, h⟩
  cases l <;> cases m <;> cases h <;> cases t <;> decide

theorem select_highest (a : Active) (t u : Task) :
    select a = some t → a.get u = true → priority u ≤ priority t := by
  rcases a with ⟨l, m, h⟩
  cases l <;> cases m <;> cases h <;> cases t <;> cases u <;> decide

theorem select_none_iff (a : Active) :
    select a = none ↔ a = ⟨false, false, false⟩ := by
  rcases a with ⟨l, m, h⟩
  cases l <;> cases m <;> cases h <;> decide

theorem activate_preserves (s : State) (target : Option Task) (hv : Valid s) :
    Valid (activate s target).state := by
  cases target with
  | none => exact hv
  | some t =>
    by_cases ha : s.active.get t = true
    · simpa [activate, ha] using hv
    · simp [activate, ha, schedule, Valid]

theorem terminate_preserves (s : State) (hv : Valid s) :
    Valid (terminate s).state := by
  unfold terminate
  split
  · exact hv
  · exact schedule_valid _

theorem running_current (s : State) (t : Task) (hv : Valid s) :
    taskState s t = .running ↔ s.current = some t := by
  rcases s with ⟨⟨l, m, h⟩, cur⟩
  cases l <;> cases m <;> cases h <;>
    simp_all [Valid, select] <;> cases t <;> decide

theorem at_most_one_running (s : State) (t u : Task) (hv : Valid s)
    (ht : taskState s t = .running) (hu : taskState s u = .running) : t = u := by
  have ht' := (running_current s t hv).mp ht
  have hu' := (running_current s u hv).mp hu
  exact Option.some.inj (ht'.symm.trans hu')

theorem active_state_consistent (s : State) (t : Task) :
    s.active.get t = true ↔ taskState s t ≠ .suspended := by
  unfold taskState
  cases hg : s.active.get t <;> simp [hg]
  split <;> decide

theorem activation_limit (s : State) (t : Task) (h : s.active.get t = true) :
    activate s (some t) = ⟨s, .returned .limit⟩ := by
  simp [activate, h]

theorem invalid_activation (s : State) :
    activate s none = ⟨s, .returned .id⟩ := rfl

theorem activation_error_frame (s : State) (target : Option Task) (e : Status)
    (he : e ≠ .ok) (hc : (activate s target).control = .returned e) :
    (activate s target).state = s := by
  cases target with
  | none => rfl
  | some t =>
    by_cases ha : s.active.get t = true
    · simp [activate, ha]
    · simp [activate, ha] at hc
      exact False.elim (he hc.symm)

theorem activation_success (s : State) (t : Task) (h : s.active.get t = false) :
    (activate s (some t)).state.active.get t = true := by
  cases t <;> simp_all [activate, schedule, Active.get, Active.set]

theorem activation_other_active (s : State) (t u : Task) (hne : u ≠ t) :
    (activate s (some t)).state.active.get u = s.active.get u := by
  cases t <;> cases u <;> simp_all [activate, schedule, Active.get, Active.set]
  all_goals split <;> rfl

theorem preemption (s : State) (t : Task) (h : s.active.get t = false) :
    (activate s (some t)).state.current = select (s.active.set t true) := by
  simp [activate, h, schedule]

theorem termination_dispatch (s : State) (t : Task) (h : s.current = some t) :
    (terminate s).control = .dispatch (select (s.active.set t false)) := by
  simp [terminate, h, schedule]

theorem termination_suspends (s : State) (t : Task) (h : s.current = some t) :
    taskState (terminate s).state t = .suspended := by
  cases t <;> simp [terminate, h, taskState, schedule, Active.set, Active.get]

theorem termination_other_active (s : State) (t u : Task)
    (hc : s.current = some t) (hne : u ≠ t) :
    (terminate s).state.active.get u = s.active.get u := by
  cases t <;> cases u <;>
    simp_all [terminate, schedule, Active.get, Active.set]

theorem termination_error_frame (s : State) (h : s.current = none) :
    terminate s = ⟨s, .returned .callevel⟩ := by simp [terminate, h]

/- A scheduling operation may legitimately change the old and new runner's
   derived task state. Unrelated active membership must not change. -/
theorem unrelated_task_state (s s' : State) (t : Task)
    (ha : s'.active.get t = s.active.get t)
    (hc : s.current ≠ some t) (hc' : s'.current ≠ some t) :
    taskState s' t = taskState s t := by
  simp [taskState, ha, hc, hc']

theorem get_id_correct (s : State) : getTaskID s = (.ok, s.current) := rfl
theorem get_state_correct (s : State) (t : Task) :
    getTaskState s (some t) = (.ok, some (taskState s t)) := rfl
theorem get_state_invalid (s : State) : getTaskState s none = (.id, none) := rfl

theorem initial_suspended (t : Task) : taskState initial t = .suspended := by
  cases t <;> decide

inductive Command where
  | activate (target : Option Task)
  | terminate
  deriving Repr

def transition (s : State) : Command → State
  | .activate t => (activate s t).state
  | .terminate => (terminate s).state

def execute (s : State) : List Command → State
  | [] => s
  | c :: cs => execute (transition s c) cs

theorem transition_preserves (s : State) (c : Command) (h : Valid s) :
    Valid (transition s c) := by
  cases c with
  | activate t => exact activate_preserves s t h
  | terminate => exact terminate_preserves s h

theorem execution_preserves (cs : List Command) (s : State) (h : Valid s) :
    Valid (execute s cs) := by
  induction cs generalizing s with
  | nil => exact h
  | cons c cs ih => exact ih _ (transition_preserves s c h)

theorem reachable_valid (cs : List Command) : Valid (execute initial cs) :=
  execution_preserves cs initial initial_valid

end LeanCpOs
