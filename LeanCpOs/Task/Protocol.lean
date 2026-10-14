import LeanCpOs.Task.Model

namespace LeanCpOs.TaskControl

/- One input line is a complete independent trace:
   N (priority activationLimit preemptive)* K (operation target context)*.
   Preemptive is 0 or 1. Task ids are zero-based. N and limits are positive.
   Operations: Activate=0, Terminate=1, Chain=2, Schedule=3, GetID=4,
   GetState=5, model progress=6, ISR entry=7, ISR exit=8.
   Context: task=0, ISR2=1, unsupported=2/3; +4 means resources held.

   One output line per operation:
   status currentIdPlus1 discard value readyCount (taskIdPlus1 pc)*
   currentPc isrDepth.
   Status: OK=0, ID=1, LIMIT=2, CALLEVEL=3, RESOURCE=4, BADINPUT=5.
   Task state value: suspended=1, ready=2, running=3; GetID uses id+1,
   with zero for idle. A malformed entire input line produces INVALID.

   The command format is a testing interface, not the OSEK C ABI. -/
structure Command where
  op : Nat
  target : Nat
  context : Nat
  deriving Repr

def parseConfig : Nat → List Nat → Option (Config × List Nat)
  | 0, xs => some ([], xs)
  | n + 1, p :: limit :: preempt :: xs => do
    if limit == 0 || preempt > 1 then none else do
      let (cfg, rest) ← parseConfig n xs
      return (⟨p, limit, preempt == 1⟩ :: cfg, rest)
  | _, _ => none

def parseCommands : Nat → List Nat → Option (List Command)
  | 0, [] => some []
  | n + 1, op :: target :: ctx :: xs => do
    let rest ← parseCommands n xs
    return ⟨op, target, ctx⟩ :: rest
  | _, _ => none

def parseTrace (line : String) : Option (Config × List Command) := do
  let fields := ((line.replace "\t" " ").replace "\r" " ").trim.splitOn " "
  let numbers ← (fields.filter (fun f => !f.isEmpty)).mapM String.toNat?
  match numbers with
  | n :: xs =>
    if n == 0 then none else do
      let (cfg, rest) ← parseConfig n xs
      match rest with
      | k :: xs => return (cfg, ← parseCommands k xs)
      | [] => none
  | [] => none

def statusCode : Status → Nat
  | .ok => 0 | .id => 1 | .limit => 2 | .callevel => 3
  | .resource => 4 | .badInput => 5

def resultNumbers (r : Result) : List Nat :=
  [statusCode r.status, (r.state.current.map (fun f => f.task + 1)).getD 0,
    if r.discard then 1 else 0, r.value, r.state.ready.length] ++
  r.state.ready.flatMap (fun f => [f.task + 1, f.pc]) ++
  [(r.state.current.map Frame.pc).getD 0, r.state.isrDepth]

def renderResult (r : Result) : String :=
  String.intercalate " " ((resultNumbers r).map toString)

def runTrace (cfg : Config) : State → List Command → List Result
  | _, [] => []
  | s, cmd :: cmds =>
    let r := step cfg s cmd.op cmd.target cmd.context
    r :: runTrace cfg r.state cmds

end LeanCpOs.TaskControl
