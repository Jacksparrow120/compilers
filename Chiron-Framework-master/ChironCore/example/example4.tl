:a = 5
:b = 10
if (:a != :b) [
  :temp = :a
  :a = :b
  :b = :temp
]
forward :a
forward :b