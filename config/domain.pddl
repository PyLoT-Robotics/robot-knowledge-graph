;; ==============================================================================
;; PyLoT RoboCup 2025 - 基本タスクプラニング用 PDDL ドメイン定義
;; ナレッジグラフと連携してタスクの検証 (Validator) やプラニングに使用する
;;
;; [概説] PDDL (Planning Domain Definition Language) とは
;;   - AIにおける自動プランニング用の標準記述言語です。
;;   - ドメイン(Domain)定義: 「世界にどんな種類の物体があるか（types）」「どんな状態が存在しうるか（predicates）」「どんな行動が取れるか（actions）」という、環境のルールを定義します。
;;   - 問題(Problem)定義: ドメイン定義されたルールを使って、「初期状態（init）」から「目標状態（goal）」へ到達する手順を解かせます。
;; ==============================================================================

(define (domain pylot_domain)

  ;; ----------------------------------------------------------------------------
  ;; 1. REQUIREMENTS (要件定義)
  ;;   このドメインを解くためにプランナー（ソルバ）がサポートすべき機能を指定します。
  ;;   - :typing               オブジェクトが型 (type) を持つことを許容します。
  ;;   - :negative-preconditions 前提条件(precondition)に否定(not)を書くことを許容します。
  ;;   - :strips               最も基本的なプランニング表現（前提条件を満たせば効果が発動する）をサポートします。
  ;; ----------------------------------------------------------------------------
  (:requirements :typing :negative-preconditions :strips)

  ;; ----------------------------------------------------------------------------
  ;; 2. TYPES (型の定義)
  ;;   オブジェクトの階層構造を定義します。
  ;;   例えば `robot room furniture object - item` は、
  ;;   「robot, room, furniture, object はすべて item (アイテム) という大きな括りの一部分である」という意味の継承関係を構築します。
  ;;   これにより、述語の引数などで型の制約をつけやすくなります（例: 「room 型の変数しか受け付けない」など）。
  ;; ----------------------------------------------------------------------------
  (:types
    robot room furniture object - item
  )

  ;; ----------------------------------------------------------------------------
  ;; 3. PREDICATES (述語の定義)
  ;;   世界を表現する「状態（真偽値で表される事実）」のリストです。
  ;;   これらが「成り立っているか (True) 」「成り立っていないか (False) 」の組み合わせが、ロボットがいる現在の世界の状態そのものになります。
  ;;   - 引数には `?変数名 - 型` の形式で、どんなオブジェクトを受け取るかを定義します。
  ;; ----------------------------------------------------------------------------
  (:predicates
    ;; 特定の部屋 ?r1 と部屋 ?r2 が繋がっているか
    (connected_to ?r1 - room ?r2 - room)
    ;; 家具 ?f が部屋 ?r の中にあるか
    (is_in ?f - furniture ?r - room)
    ;; 物体 ?o が家具 ?f の上にあるか
    (on_top_of ?o - object ?f - furniture)
    ;; ロボット ?r がアイテム ?loc (部屋や家具などの場所) にいるか
    (robot_at ?r - robot ?loc - item)
    ;; ロボット ?r が物体 ?o を持っている（把持している）状態か
    (holding ?r - robot ?o - object)
    ;; ロボット ?r の手が空いている状態か
    (hand_empty ?r - robot)
  )

  ;; ----------------------------------------------------------------------------
  ;; 4. ACTIONS (行動の定義)
  ;;   ロボットが実行可能なアクションと、その条件・結果を定義します。
  ;;   [構成要素]
  ;;   - :parameters   このアクションを実行する際に必要な引数（関係するオブジェクト）。
  ;;   - :precondition アクションを実行するための「前提条件」（現在の状態でこれらが全て真(True)である必要がある）。
  ;;   - :effect       アクションを実行した「結果」（状態がどのように変化するかを定義。not をつけると元の状態が偽(False)に消去される）。
  ;; ----------------------------------------------------------------------------

  ;; アクション: ロボットの部屋間移動
  (:action move_room
    :parameters (?rob - robot ?from - room ?to - room)
    :precondition (and
      (robot_at ?rob ?from)     ;; 前提: ロボットが移動元の部屋(?from)にいること
      (connected_to ?from ?to)  ;; 前提: 移動元(?from)と移動先(?to)が繋がっていること
    )
    :effect (and
      (not (robot_at ?rob ?from)) ;; 結果: ロボットは移動元の部屋からいなくなる
      (robot_at ?rob ?to)         ;; 結果: ロボットは移動先の部屋に到着する
    )
  )

  ;; アクション: 部屋内で家具へアプローチ
  (:action approach_furniture
    :parameters (?rob - robot ?r - room ?f - furniture)
    :precondition (and
      (robot_at ?rob ?r) ;; 前提: ロボットが家具のある部屋(?r)にいること
      (is_in ?f ?r)      ;; 前提: 目標の家具(?f)がその部屋(?r)にあること
    )
    :effect (and
      (not (robot_at ?rob ?r)) ;; 結果: （位置情報の粒度が変わるため）部屋への大まかな位置情報を消去
      (robot_at ?rob ?f)       ;; 結果: ロボットの現在位置が家具(?f)の前に明確に更新される
    )
  )

  ;; アクション: 物体を掴む
  (:action pick
    :parameters (?rob - robot ?obj - object ?f - furniture)
    :precondition (and
      (robot_at ?rob ?f)       ;; 前提: ロボットが物体のある家具(?f)の前にいること
      (on_top_of ?obj ?f)      ;; 前提: 物体(?obj)が家具(?f)の上にあること
      (hand_empty ?rob)        ;; 前提: ロボットの手が空いていること
    )
    :effect (and
      (not (hand_empty ?rob))  ;; 結果: ロボットの手は空ではなくなる
      (holding ?rob ?obj)      ;; 結果: ロボットは物体(?obj)を保持した状態になる
      (not (on_top_of ?obj ?f)) ;; 結果: 物体は家具の上から無くなる
    )
  )

  ;; アクション: 物体を置く
  (:action place
    :parameters (?rob - robot ?obj - object ?f - furniture)
    :precondition (and
      (robot_at ?rob ?f)       ;; 前提: ロボットが目標の家具(?f)の前にいること
      (holding ?rob ?obj)      ;; 前提: ロボットが物体(?obj)を保持していること
    )
    :effect (and
      (hand_empty ?rob)        ;; 結果: ロボットの手が空く
      (not (holding ?rob ?obj)) ;; 結果: ロボットは物体を保持しなくなる
      (on_top_of ?obj ?f)      ;; 結果: 物体が家具(?f)の上に置かれる
    )
  )
)
