import LeanCpOs.Task.Protocol

def main : IO Unit := do
  let stdin ← IO.getStdin
  let stdout ← IO.getStdout
  repeat
    let line ← stdin.getLine
    if line.isEmpty then break
    match LeanCpOs.TaskControl.parseTrace line with
    | none => stdout.putStrLn "INVALID"
    | some (cfg, commands) =>
      for result in LeanCpOs.TaskControl.runTrace cfg LeanCpOs.TaskControl.initial commands do
        stdout.putStrLn (LeanCpOs.TaskControl.renderResult result)
