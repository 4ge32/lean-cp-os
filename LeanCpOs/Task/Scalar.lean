/- Bounded target adapter. All scheduling decisions compile from this Lean source.
   Its correspondence with the arbitrary-size model is differential-tested, not proved.
   Four tasks, at most eight activation frames in total; priorities 0..15.
   Config: priorities[16], activation limits[16], preemptive mask[4], count[4].
   State: FIFO task codes[32], current code[4], modeled ISR depth[4].
   Result: state[40], status[4], value[4], discard[1]. Task code = id+1; 0 = none.
-/
namespace LeanCpOs.Task.Scalar

abbrev Word := UInt64

def nibble (w i : Word) : Word := (w >>> (4 * i)) &&& 15
def taskCount (cfg : Word) : Word := nibble cfg 9
def priority (cfg code : Word) : Word := if code == 0 then 0 else nibble cfg (code - 1)
def limit (cfg code : Word) : Word := nibble cfg (code + 3)
def preemptive (cfg code : Word) : Bool := ((cfg >>> (31 + code)) &&& 1) == 1
def queue (s : Word) : Word := s &&& 4294967295
def current (s : Word) : Word := nibble s 8
def depth (s : Word) : Word := nibble s 9
def state (q c d : Word) : Word := q ||| (c <<< 32) ||| (d <<< 36)
def result (s e v : Word) (discard : Bool := false) : Word :=
  s ||| (e <<< 40) ||| (v <<< 44) ||| (if discard then 281474976710656 else 0)

def chooseAt (cfg q best i : Word) : Word :=
  let code := nibble q i
  if code == 0 then best
  else if best == 8 || priority cfg code > priority cfg (nibble q best) then i
  else best

def choose (cfg q : Word) : Word :=
  let b := chooseAt cfg q 8 0
  let b := chooseAt cfg q b 1
  let b := chooseAt cfg q b 2
  let b := chooseAt cfg q b 3
  let b := chooseAt cfg q b 4
  let b := chooseAt cfg q b 5
  let b := chooseAt cfg q b 6
  chooseAt cfg q b 7

def removeAt (q i : Word) : Word :=
  let lowMask := (1 <<< (4 * i)) - 1
  (q &&& lowMask) ||| ((q >>> (4 * (i + 1))) <<< (4 * i))

def length (q : Word) : Word :=
  (if nibble q 0 == 0 then 0 else 1) + (if nibble q 1 == 0 then 0 else 1) +
  (if nibble q 2 == 0 then 0 else 1) + (if nibble q 3 == 0 then 0 else 1) +
  (if nibble q 4 == 0 then 0 else 1) + (if nibble q 5 == 0 then 0 else 1) +
  (if nibble q 6 == 0 then 0 else 1) + (if nibble q 7 == 0 then 0 else 1)

def count (q code : Word) : Word :=
  (if nibble q 0 == code then 1 else 0) + (if nibble q 1 == code then 1 else 0) +
  (if nibble q 2 == code then 1 else 0) + (if nibble q 3 == code then 1 else 0) +
  (if nibble q 4 == code then 1 else 0) + (if nibble q 5 == code then 1 else 0) +
  (if nibble q 6 == code then 1 else 0) + (if nibble q 7 == code then 1 else 0)

def activeCount (s code : Word) : Word := count (queue s) code + (if current s == code then 1 else 0)
def append (q code : Word) : Word := q ||| (code <<< (4 * length q))

def configTaskValid (cfg code : Word) : Bool :=
  if code ≤ taskCount cfg then limit cfg code > 0 && limit cfg code ≤ 8
  else limit cfg code == 0 && priority cfg code == 0 && !preemptive cfg code

def configValid (cfg : Word) : Bool :=
  cfg < 1099511627776 && taskCount cfg > 0 && taskCount cfg ≤ 4 &&
  configTaskValid cfg 1 && configTaskValid cfg 2 &&
  configTaskValid cfg 3 && configTaskValid cfg 4 &&
  limit cfg 1 + limit cfg 2 + limit cfg 3 + limit cfg 4 ≤ 8

def slotValid (cfg q i : Word) : Bool :=
  nibble q i ≤ taskCount cfg && (i == 0 || nibble q i == 0 || nibble q (i-1) != 0)
def countsValid (cfg s code : Word) : Bool :=
  activeCount s code ≤ limit cfg code

def stateValid (cfg s : Word) : Bool :=
  s < 1099511627776 && current s ≤ taskCount cfg &&
  slotValid cfg (queue s) 0 && slotValid cfg (queue s) 1 &&
  slotValid cfg (queue s) 2 && slotValid cfg (queue s) 3 &&
  slotValid cfg (queue s) 4 && slotValid cfg (queue s) 5 &&
  slotValid cfg (queue s) 6 && slotValid cfg (queue s) 7 &&
  countsValid cfg s 1 && countsValid cfg s 2 && countsValid cfg s 3 && countsValid cfg s 4

/-- Dispatch a waiting highest-priority frame, or remain idle. -/
def dispatch (cfg q d : Word) : Word :=
  let i := choose cfg q
  if i == 8 then state q 0 d else state (removeAt q i) (nibble q i) d

/-- Only a strictly higher priority task preempts; interrupted frame stays first among peers. -/
def reschedule (cfg s : Word) (explicit : Bool := false) : Word :=
  if depth s != 0 then s
  else if current s == 0 then dispatch cfg (queue s) 0
  else if !explicit && !preemptive cfg (current s) then s
  else
    let i := choose cfg (queue s)
    if i == 8 || priority cfg (nibble (queue s) i) ≤ priority cfg (current s) then s
    else state ((removeAt (queue s) i <<< 4) ||| current s) (nibble (queue s) i) 0

/-- Context: 0 task, 1 ISR2, 2 unsupported; bit 2 records held resources. -/
def contextValid (s ctx : Word) : Bool :=
  (ctx &&& 3) == (if depth s == 0 then 0 else 1) && ctx < 8

def taskContext (s ctx : Word) : Bool := contextValid s ctx && (ctx &&& 3) == 0 && current s != 0

@[export lean_osek_step]
def step (cfg s op id ctx : Word) : Word :=
  -- Literal BADINPUT/zero-state avoids a generated module-initialization dependency.
  if !configValid cfg || !stateValid cfg s then 5497558138880
  else if op == 7 then
    if depth s == 15 then result s 5 0
    else result (state (queue s) (current s) (depth s + 1)) 0 0
  else if op == 8 then
    if depth s == 0 then result s 3 0
    else
      let t := reschedule cfg (state (queue s) (current s) (depth s - 1))
      result t 0 0
  else if op > 5 then result s 5 0
  else if !contextValid s ctx then result s 3 0
  else if op == 0 then
    if depth s == 0 && current s == 0 then result s 3 0
    else if id ≥ taskCount cfg then result s 1 0
    else if activeCount s (id + 1) ≥ limit cfg (id + 1) then result s 2 0
    else
      let t := reschedule cfg (state (append (queue s) (id+1)) (current s) (depth s))
      result t 0 0
  else if op == 1 || op == 2 || op == 3 then
    if !taskContext s ctx then result s 3 0
    else if (ctx &&& 4) != 0 then result s 4 0
    else if op == 3 then
      let t := reschedule cfg s true
      result t 0 0
    else if op == 1 then result (dispatch cfg (queue s) 0) 0 0 true
    else if id ≥ taskCount cfg then result s 1 0
    else if id + 1 != current s && activeCount s (id+1) ≥ limit cfg (id+1) then result s 2 0
    else result (dispatch cfg (append (queue s) (id+1)) 0) 0 0 true
  else if op == 4 then result s 0 (current s)
  else if op == 5 then
    if id ≥ taskCount cfg then result s 1 0
    else result s 0 (if current s == id+1 then 3 else if count (queue s) (id+1) > 0 then 2 else 1)
  else result s 5 0

end LeanCpOs.Task.Scalar
