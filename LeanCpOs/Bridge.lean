import LeanCpOs.Model
namespace LeanCpOs

def decodeTask (n : Nat) : Option Task :=
  match n with | 0 => some .low | 1 => some .mid | 2 => some .high | _ => none
def taskCode : Option Task → Nat
  | none => 0 | some .low => 1 | some .mid => 2 | some .high => 3
def statusCode : Status → Nat
  | .ok => 0 | .id => 1 | .limit => 2 | .callevel => 3 | .badInput => 4
def stateCode : Option TaskState → Nat
  | none => 0 | some .suspended => 1 | some .ready => 2 | some .running => 3
def fromMask (n : Nat) : State :=
  schedule ⟨n % 2 == 1, n / 2 % 2 == 1, n / 4 % 2 == 1⟩
def toMask (a : Active) : Nat :=
  (if a.low then 1 else 0) + (if a.mid then 2 else 0) + (if a.high then 4 else 0)
def pack (s : State) (e : Status) (dispatch : Bool) (value : Nat) : UInt64 :=
  UInt64.ofNat (toMask s.active + 16 * taskCode s.current +
    256 * statusCode e + (if dispatch then 4096 else 0) + 65536 * value)
def packResult (r : Result) : UInt64 :=
  match r.control with
  | .returned e => pack r.state e false 0
  | .dispatch _ => pack r.state .ok true 0

/- Experimental scalar ABI, NOT AUTOSAR StatusType or pointer ABI.
   The mask encodes a canonical state. Invalid masks are rejected, not truncated. -/
@[export lean_cp_step]
def step (mask op id : UInt32) : UInt64 :=
  let s := fromMask mask.toNat
  if mask.toNat ≥ 8 then pack initial .badInput false 0
  else match op.toNat with
  | 0 => packResult (activate s (decodeTask id.toNat))
  | 1 => packResult (terminate s)
  | 2 => let (e, t) := getTaskID s; pack s e false (taskCode t)
  | 3 => let (e, t) := getTaskState s (decodeTask id.toNat); pack s e false (stateCode t)
  | _ => pack s .badInput false 0

end LeanCpOs
