import LeanCpOs.Proofs

namespace Book.Proofs
open LeanCpOs

-- 一つの具体例: low を起動し、high に中断され、low に戻る。
def commands : List Command :=
  [.activate (some .low), .activate (some .high), .terminate]

def observed : State := execute initial commands
#guard observed.current = some .low
#guard Valid observed
#eval observed.current

-- 具体例の正しさを、任意長の操作列についての定理から得る。
theorem observed_valid : Valid observed :=
  reachable_valid commands

-- 「任意の cs」に対して、実行中だと言える二つのタスクは同じ。
theorem one_runner_after (cs : List Command) (t u : Task)
    (ht : taskState (execute initial cs) t = .running)
    (hu : taskState (execute initial cs) u = .running) : t = u := by
  have hv : Valid (execute initial cs) := reachable_valid cs
  exact at_most_one_running (execute initial cs) t u hv ht hu

-- Valid を満たさない State も、型だけなら作れてしまう。
def inconsistent : State := ⟨⟨true, false, false⟩, some .high⟩
#guard ¬ Valid inconsistent
#guard taskState inconsistent .high = .suspended

-- 演習の解答: 終了の後にもう一度 high を起動する。
def extended : List Command := commands ++ [.activate (some .high)]
#guard (execute initial extended).current = some .high
example : Valid (execute initial extended) := reachable_valid extended

-- 個々のタスクを列挙せず、既存の証明を一段組み合わせる。
theorem valid_after_another_activation (cs : List Command) (target : Option Task) :
    Valid (activate (execute initial cs) target).state := by
  exact activate_preserves _ target (reachable_valid cs)

end Book.Proofs
