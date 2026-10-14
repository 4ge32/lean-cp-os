import LeanCpOs.Task.Semantics

open LeanCpOs.TaskControl

namespace Book.Change

-- Task 0 continues its work; task 1 handles requests at a higher priority.
def baseline : Config := [⟨1, 1, true⟩, ⟨3, 1, true⟩]
def revised : Config := [⟨1, 1, true⟩, ⟨3, 2, true⟩]

-- A deliberately explicit starting state, not a StartOS implementation.
def seed : State := { current := some ⟨0, 7⟩ }

def oldFirst := activate baseline seed 1 0
def oldSecond := activate baseline oldFirst.state 1 0
#guard oldFirst.status == .ok
#guard oldSecond.status == .limit
#guard oldSecond.state == oldFirst.state

def first := activate revised seed 1 0
def progressed := stepPc first.state 0
def second := activate revised progressed.state 1 0
def third := activate revised second.state 1 0
#guard first.status == .ok
#guard progressed.state.current == some ⟨1, 1⟩
#guard second.status == .ok
#guard activeCount second.state 1 == 2
#guard second.state.current == some ⟨1, 1⟩
#guard second.state.ready == [⟨0, 7⟩, ⟨1, 0⟩]
#guard third.status == .limit
#guard third.state == second.state
#guard third.discard == false

-- Completing request 1 starts request 2 from the beginning.
def finishFirst := terminate revised second.state 0
#guard finishFirst.status == .ok
#guard finishFirst.discard == true
#guard finishFirst.state.current == some ⟨1, 0⟩
#guard activeCount finishFirst.state 1 == 1

-- Completing request 2 resumes the interrupted task at its saved progress.
def finishSecond := terminate revised finishFirst.state 0
#guard finishSecond.status == .ok
#guard finishSecond.discard == true
#guard finishSecond.state.current == some ⟨0, 7⟩
#guard activeCount finishSecond.state 1 == 0

-- Reuse the service contract for this configuration and arbitrary states.
example (s : State) (h : (activate revised s 1 0).status ≠ .ok) :
    (activate revised s 1 0).state = s :=
  activate_error_unchanged revised s 1 0 h

end Book.Change
