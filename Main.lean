import LeanCpOs.Bridge

def main : IO Unit := do
  let stdin ← IO.getStdin
  let stdout ← IO.getStdout
  repeat
    let line ← stdin.getLine
    if line.isEmpty then break
    let fields := line.trim.splitOn " "
    match fields with
    | [m, o, i] =>
      match m.toNat?, o.toNat?, i.toNat? with
      | some m, some o, some i =>
        if m > 4294967295 || o > 4294967295 || i > 4294967295 then
          throw (IO.userError "uint32 overflow")
        let r := LeanCpOs.step m.toUInt32 o.toUInt32 i.toUInt32
        stdout.putStrLn s!"{r.toNat}"
      | _, _, _ => throw (IO.userError "invalid vector")
    | _ => throw (IO.userError "expected three integers")
