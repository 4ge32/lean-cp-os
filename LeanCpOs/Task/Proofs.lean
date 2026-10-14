import LeanCpOs.Task.Model

namespace LeanCpOs.TaskControl

set_option maxRecDepth 4096
set_option maxHeartbeats 2000000

/- Supply the constructive natural-number equality laws directly. -/
local instance lawfulNatBEq : LawfulBEq Nat where
  eq_of_beq := fun h => of_decide_eq_true h
  rfl := decide_eq_true rfl

/-- Selection returns no frame exactly when there is no queued activation. -/
theorem choose_none_iff (cfg : Config) (fs : List Frame) :
    choose cfg fs = none ↔ fs = [] := by
  cases fs with
  | nil => simp [choose]
  | cons f fs =>
    cases hc : choose cfg fs with
    | none => simp [choose, hc]
    | some p =>
      rcases p with ⟨best, rest⟩
      simp only [choose, hc]
      split <;> simp

/-- Selecting a runnable activation neither loses nor duplicates any frame. -/
theorem choose_perm (cfg : Config) (fs : List Frame) (f : Frame) (rest : List Frame)
    (h : choose cfg fs = some (f, rest)) : List.Perm (f :: rest) fs := by
  induction fs generalizing f rest with
  | nil => simp [choose] at h
  | cons a as ih =>
    cases hc : choose cfg as with
    | none =>
      have ha := (choose_none_iff cfg as).mp hc
      subst as
      simp [choose] at h
      rcases h with ⟨rfl, rfl⟩
      exact .rfl
    | some p =>
      rcases p with ⟨b, bs⟩
      simp only [choose, hc] at h
      split at h
      · cases h
        exact .rfl
      · cases h
        exact (List.Perm.swap ..).trans ((ih _ _ hc).cons a)

/-- A chosen activation has at least the priority of every queued activation. -/
theorem choose_highest (cfg : Config) (fs : List Frame) (f : Frame) (rest : List Frame)
    (h : choose cfg fs = some (f, rest)) :
    ∀ u ∈ fs, priority cfg u ≤ priority cfg f := by
  induction fs generalizing f rest with
  | nil => simp [choose] at h
  | cons a as ih =>
    cases hc : choose cfg as with
    | none =>
      have ha := (choose_none_iff cfg as).mp hc
      subst as
      simp [choose] at h
      rcases h with ⟨rfl, rfl⟩
      intro u hu
      have hu := List.mem_singleton.mp hu
      subst u
      exact Nat.le_refl _
    | some p =>
      rcases p with ⟨b, bs⟩
      simp only [choose, hc] at h
      split at h
      · rename_i hp
        cases h
        intro u hu
        rcases List.mem_cons.mp hu with rfl | hu
        · exact Nat.le_refl _
        · exact Nat.le_trans (ih b bs hc u hu) hp
      · rename_i hp
        cases h
        intro u hu
        rcases List.mem_cons.mp hu with rfl | hu
        · exact Nat.le_of_lt (Nat.lt_of_not_ge hp)
        · exact ih _ _ hc u hu

/-- A head activation wins a tie with every lower or equal priority follower. -/
theorem choose_fifo_head (cfg : Config) (f : Frame) (fs : List Frame)
    (h : ∀ u ∈ fs, priority cfg u ≤ priority cfg f) :
    choose cfg (f :: fs) = some (f, fs) := by
  cases hc : choose cfg fs with
  | none =>
    have he := (choose_none_iff cfg fs).mp hc
    subst fs
    rfl
  | some p =>
    rcases p with ⟨b, bs⟩
    have hb : b ∈ fs := (choose_perm cfg fs b bs hc).mem_iff.mp (by simp)
    simp [choose, hc, h b hb]

def frames (s : State) : List Frame := s.current.toList ++ s.ready

theorem initial_valid (cfg : Config) : Valid cfg initial := by
  constructor
  · intro f hf
    exact False.elim (List.not_mem_nil hf)
  · intro t tc hc
    exact Nat.zero_le _

/-- Constructive count preservation, proved directly over list permutations. -/
theorem perm_countP {α : Type} (p : α → Bool) {xs ys : List α}
    (hp : List.Perm xs ys) : xs.countP p = ys.countP p := by
  induction hp with
  | nil => rfl
  | cons a hp ih => simp only [List.countP_cons, ih]
  | swap a b xs => simp only [List.countP_cons, Nat.add_right_comm]
  | trans hp hq ihp ihq => exact ihp.trans ihq

theorem valid_of_perm (cfg : Config) (s s' : State)
    (hp : List.Perm (frames s') (frames s)) (hv : Valid cfg s) : Valid cfg s' := by
  constructor
  · intro f hf
    exact hv.1 f (hp.mem_iff.mp hf)
  · intro t tc hc
    have he := perm_countP (fun f => f.task == t) hp
    change (frames s').countP _ ≤ _
    rw [he]
    exact hv.2 t tc hc

/-- Dispatch consumes the ready list only; callers discard the old current first. -/
theorem dispatch_perm (cfg : Config) (s : State) :
    List.Perm (frames (dispatch cfg s)) s.ready := by
  cases hc : choose cfg s.ready with
  | none => simp [dispatch, hc, frames]
  | some p =>
    rcases p with ⟨f, rest⟩
    simpa [dispatch, hc, frames] using choose_perm cfg s.ready f rest hc

theorem dispatch_valid (cfg : Config) (s : State) (hv : Valid cfg s) :
    Valid cfg (dispatch cfg s) := by
  have hp := dispatch_perm cfg s
  constructor
  · intro f hf
    exact hv.1 f (List.mem_append_right _ (hp.mem_iff.mp hf))
  · intro t tc hc
    have he := perm_countP (fun f => f.task == t) hp
    have hh := hv.2 t tc hc
    change (frames (dispatch cfg s)).countP _ ≤ _
    rw [he]
    simp only [activeCount, List.countP_append] at hh
    exact Nat.le_trans (Nat.le_add_left _ _) hh

/-- Preemption moves complete frames, preserving each activation's continuation. -/
theorem mayPreempt_perm (cfg : Config) (s : State) (explicit : Bool) :
    List.Perm (frames (mayPreempt cfg s explicit)) (frames s) := by
  unfold mayPreempt
  split
  · exact .rfl
  · cases hs : s.current with
    | none => simpa [hs, frames] using dispatch_perm cfg s
    | some running =>
      simp only
      split
      · cases hc : choose cfg s.ready with
        | none => exact .rfl
        | some p =>
          rcases p with ⟨next, rest⟩
          simp only
          split
          · simp only [frames, Option.toList_some, List.singleton_append, hs]
            exact (List.Perm.swap ..).trans ((choose_perm cfg s.ready next rest hc).cons running)
          · exact .rfl
      · exact .rfl

theorem mayPreempt_valid (cfg : Config) (s : State) (explicit : Bool)
    (hv : Valid cfg s) : Valid cfg (mayPreempt cfg s explicit) :=
  valid_of_perm cfg s _ (mayPreempt_perm cfg s explicit) hv

theorem mayPreempt_activation_count (cfg : Config) (s : State) (explicit : Bool) (t : Nat) :
    activeCount (mayPreempt cfg s explicit) t = activeCount s t := by
  exact perm_countP (fun f : Frame => f.task == t) (mayPreempt_perm cfg s explicit)

theorem append_activation_count (s : State) (target t : Nat) :
    activeCount { s with ready := s.ready ++ [⟨target, 0⟩] } t =
      activeCount s t + if target == t then 1 else 0 := by
  simp only [activeCount, List.countP_append, List.countP_singleton, Nat.add_assoc]

theorem append_activation_valid (cfg : Config) (s : State) (target : Nat) (tc : TaskConfig)
    (hv : Valid cfg s) (hc : cfg[target]? = some tc)
    (hl : activeCount s target < tc.maxActivations) :
    Valid cfg { s with ready := s.ready ++ [⟨target, 0⟩] } := by
  constructor
  · intro f hf
    simp only [List.mem_append, List.mem_singleton] at hf
    rcases hf with hf | hf | hf
    · exact hv.1 f (List.mem_append_left _ hf)
    · exact hv.1 f (List.mem_append_right _ hf)
    · subst f
      exact (List.getElem?_eq_some_iff.mp hc).1
  · intro t tc' hc'
    rw [append_activation_count]
    by_cases ht : target = t
    · subst t
      have he : tc = tc' := Option.some.inj (hc.symm.trans hc')
      subst tc'
      simp only [beq_self_eq_true, ↓reduceIte]
      exact hl
    · simp only [beq_iff_eq, ht, ↓reduceIte, Nat.add_zero]
      exact hv.2 t tc' hc'

theorem drop_current_valid (cfg : Config) (s : State) (hv : Valid cfg s) :
    Valid cfg { s with current := none } := by
  constructor
  · intro f hf
    exact hv.1 f (List.mem_append_right _ hf)
  · intro t tc hc
    have hh := hv.2 t tc hc
    simp only [activeCount, List.countP_append] at hh
    simp only [activeCount, Option.toList_none, List.nil_append]
    exact Nat.le_trans (Nat.le_add_left _ _) hh

theorem activate_valid (cfg : Config) (s : State) (target ctx : Nat) (hv : Valid cfg s) :
    Valid cfg (activate cfg s target ctx).state := by
  unfold activate
  split
  · exact hv
  · cases hc : cfg[target]? with
    | none => exact hv
    | some tc =>
      simp only
      split
      · exact hv
      · rename_i hl
        exact mayPreempt_valid cfg _ false
          (append_activation_valid cfg s target tc hv hc (Nat.lt_of_not_ge hl))

theorem terminate_valid (cfg : Config) (s : State) (ctx : Nat) (hv : Valid cfg s) :
    Valid cfg (terminate cfg s ctx).state := by
  unfold terminate
  split
  · exact hv
  · split
    · exact hv
    · exact dispatch_valid cfg _ (drop_current_valid cfg s hv)

/-- A self-chain replaces its caller activation without consuming a new slot. -/
theorem chain_self_valid (cfg : Config) (s : State) (target : Nat) (tc : TaskConfig)
    (hv : Valid cfg s) (hc : cfg[target]? = some tc)
    (hs : s.current.any (fun f => f.task == target) = true) :
    Valid cfg { s with current := none, ready := s.ready ++ [⟨target, 0⟩] } := by
  cases hr : s.current with
  | none => simp [hr] at hs
  | some running =>
    have ht : running.task = target := by simpa [hr] using hs
    apply append_activation_valid cfg { s with current := none } target tc
      (drop_current_valid cfg s hv) hc
    have hh := hv.2 target tc hc
    simp only [activeCount, hr, Option.toList_some, List.singleton_append,
      List.countP_cons, ht, beq_self_eq_true, ↓reduceIte] at hh
    exact hh

theorem chain_valid (cfg : Config) (s : State) (target ctx : Nat) (hv : Valid cfg s) :
    Valid cfg (chain cfg s target ctx).state := by
  unfold chain
  split
  · exact hv
  · split
    · exact hv
    · cases hc : cfg[target]? with
      | none => exact hv
      | some tc =>
        simp only
        split
        · exact hv
        · rename_i hl
          apply dispatch_valid
          cases hs : s.current.any (fun f => f.task == target) with
          | true => exact chain_self_valid cfg s target tc hv hc hs
          | false =>
            have hh : activeCount s target < tc.maxActivations := by
              simp only [hs, Bool.not_false, Bool.true_and, decide_eq_true_eq] at hl
              exact Nat.lt_of_not_ge hl
            have ha := append_activation_valid cfg s target tc hv hc hh
            exact drop_current_valid cfg _ ha

theorem schedule_valid (cfg : Config) (s : State) (ctx : Nat) (hv : Valid cfg s) :
    Valid cfg (schedule cfg s ctx).state := by
  unfold schedule
  split
  · exact hv
  · split
    · exact hv
    · exact mayPreempt_valid cfg s true hv

theorem getTaskID_valid (cfg : Config) (s : State) (ctx : Nat) (hv : Valid cfg s) :
    Valid cfg (getTaskID s ctx).state := by
  unfold getTaskID
  split <;> exact hv

theorem getTaskState_valid (cfg : Config) (s : State) (target ctx : Nat) (hv : Valid cfg s) :
    Valid cfg (getTaskState cfg s target ctx).state := by
  unfold getTaskState
  split
  · exact hv
  · split <;> exact hv

/-- Advancing observable progress preserves identity and all activation counts. -/
theorem stepPc_valid (cfg : Config) (s : State) (ctx : Nat) (hv : Valid cfg s) :
    Valid cfg (stepPc s ctx).state := by
  unfold stepPc
  split
  · exact hv
  · cases hs : s.current with
    | none =>
      simp only [hs, Option.map_none]
      exact drop_current_valid cfg s hv
    | some f =>
      constructor
      · intro u hu
        simp only [hs] at hu
        change u ∈ { f with pc := f.pc + 1 } :: s.ready at hu
        simp only [List.mem_cons] at hu
        rcases hu with rfl | hu
        · apply hv.1 f
          rw [hs]
          exact List.mem_cons_self
        · exact hv.1 u (List.mem_append_right _ hu)
      · intro t tc hc
        simp only [activeCount, hs]
        change ({ f with pc := f.pc + 1 } :: s.ready).countP _ ≤ _
        rw [List.countP_cons]
        simpa only [activeCount, hs, Option.toList_some, List.singleton_append,
          List.countP_cons] using hv.2 t tc hc

theorem enterISR_valid (cfg : Config) (s : State) (hv : Valid cfg s) :
    Valid cfg (enterISR s).state := hv

theorem exitISR_valid (cfg : Config) (s : State) (hv : Valid cfg s) :
    Valid cfg (exitISR cfg s).state := by
  unfold exitISR
  split
  · exact hv
  · exact mayPreempt_valid cfg _ false hv

/-- Every command preserves valid identifiers and configured activation bounds. -/
theorem step_valid (cfg : Config) (s : State) (op target ctx : Nat) (hv : Valid cfg s) :
    Valid cfg (step cfg s op target ctx).state := by
  unfold step
  split
  · exact activate_valid cfg s target ctx hv
  · exact terminate_valid cfg s ctx hv
  · exact chain_valid cfg s target ctx hv
  · exact schedule_valid cfg s ctx hv
  · exact getTaskID_valid cfg s ctx hv
  · exact getTaskState_valid cfg s target ctx hv
  · exact stepPc_valid cfg s ctx hv
  · exact enterISR_valid cfg s hv
  · exact exitISR_valid cfg s hv
  · exact hv

def execute (cfg : Config) (s : State) : List (Nat × Nat × Nat) → State
  | [] => s
  | (op, target, ctx) :: commands => execute cfg (step cfg s op target ctx).state commands

/-- Induction covers traces of arbitrary length, not only the executable test corpus. -/
theorem execute_valid (cfg : Config) (s : State) (commands : List (Nat × Nat × Nat))
    (hv : Valid cfg s) : Valid cfg (execute cfg s commands) := by
  induction commands generalizing s with
  | nil => exact hv
  | cons command commands ih =>
    rcases command with ⟨op, target, ctx⟩
    exact ih _ (step_valid cfg s op target ctx hv)

theorem reachable_valid (cfg : Config) (commands : List (Nat × Nat × Nat)) :
    Valid cfg (execute cfg initial commands) :=
  execute_valid cfg initial commands (initial_valid cfg)

/-- A derived running task is precisely the single current frame's identity. -/
theorem running_iff (s : State) (t : Nat) :
    taskState s t = 3 ↔ ∃ f, s.current = some f ∧ f.task = t := by
  cases hc : s.current with
  | none =>
    constructor
    · intro h
      unfold taskState at h
      simp only [hc, Option.any_none, Bool.false_eq_true, ↓reduceIte] at h
      split at h <;> contradiction
    · rintro ⟨f, hf, ht⟩
      cases hf
  | some f =>
    constructor
    · intro h
      refine ⟨f, rfl, ?_⟩
      unfold taskState at h
      simp only [hc, Option.any_some, beq_iff_eq] at h
      split at h
      · assumption
      · split at h <;> contradiction
    · rintro ⟨g, hg, ht⟩
      have he := Option.some.inj hg
      subst g
      simp only [taskState, hc, Option.any_some, ht, beq_self_eq_true, ↓reduceIte]

theorem at_most_one_running (s : State) (t u : Nat)
    (ht : taskState s t = 3) (hu : taskState s u = 3) : t = u := by
  rcases (running_iff s t).mp ht with ⟨f, hf, hft⟩
  rcases (running_iff s u).mp hu with ⟨g, hg, hgu⟩
  have hfg := Option.some.inj (hf.symm.trans hg)
  cases hfg
  exact hft.symm.trans hgu

end LeanCpOs.TaskControl
