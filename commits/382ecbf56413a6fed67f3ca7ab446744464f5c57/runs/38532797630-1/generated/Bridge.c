// Lean compiler output
// Module: LeanCpOs.Bridge
// Imports: Init LeanCpOs.Model
#include <lean/lean.h>
#if defined(__clang__)
#pragma clang diagnostic ignored "-Wunused-parameter"
#pragma clang diagnostic ignored "-Wunused-label"
#elif defined(__GNUC__) && !defined(__CLANG__)
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wunused-label"
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
#endif
#ifdef __cplusplus
extern "C" {
#endif
lean_object* l_LeanCpOs_schedule(lean_object*);
lean_object* lean_uint32_to_nat(uint32_t);
uint64_t lean_uint64_of_nat(lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_fromMask(lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_decodeTask(lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_pack___boxed(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_statusCode(uint8_t);
LEAN_EXPORT lean_object* l_LeanCpOs_taskCode(lean_object*);
LEAN_EXPORT uint64_t lean_cp_step(uint32_t, uint32_t, uint32_t);
static lean_object* l_LeanCpOs_decodeTask___closed__3;
static lean_object* l_LeanCpOs_decodeTask___closed__2;
static lean_object* l_LeanCpOs_decodeTask___closed__1;
lean_object* lean_nat_div(lean_object*, lean_object*);
static uint64_t l_LeanCpOs_step___closed__1;
LEAN_EXPORT lean_object* l_LeanCpOs_decodeTask___boxed(lean_object*);
lean_object* l_LeanCpOs_terminate(lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_stateCode(lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_stateCode___boxed(lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_toMask(lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_taskCode___boxed(lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_step___boxed(lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_packResult___boxed(lean_object*);
uint8_t lean_nat_dec_eq(lean_object*, lean_object*);
lean_object* lean_nat_mod(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_fromMask___boxed(lean_object*);
lean_object* lean_nat_mul(lean_object*, lean_object*);
lean_object* l_LeanCpOs_getTaskState(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_toMask___boxed(lean_object*);
lean_object* l_LeanCpOs_activate(lean_object*, lean_object*);
lean_object* l_LeanCpOs_getTaskID(lean_object*);
LEAN_EXPORT uint64_t l_LeanCpOs_packResult(lean_object*);
LEAN_EXPORT lean_object* l_LeanCpOs_statusCode___boxed(lean_object*);
uint8_t lean_nat_dec_le(lean_object*, lean_object*);
LEAN_EXPORT uint64_t l_LeanCpOs_pack(lean_object*, uint8_t, uint8_t, lean_object*);
lean_object* lean_nat_add(lean_object*, lean_object*);
extern lean_object* l_LeanCpOs_initial;
static lean_object* _init_l_LeanCpOs_decodeTask___closed__1() {
_start:
{
uint8_t x_1; lean_object* x_2; lean_object* x_3; 
x_1 = 2;
x_2 = lean_box(x_1);
x_3 = lean_alloc_ctor(1, 1, 0);
lean_ctor_set(x_3, 0, x_2);
return x_3;
}
}
static lean_object* _init_l_LeanCpOs_decodeTask___closed__2() {
_start:
{
uint8_t x_1; lean_object* x_2; lean_object* x_3; 
x_1 = 1;
x_2 = lean_box(x_1);
x_3 = lean_alloc_ctor(1, 1, 0);
lean_ctor_set(x_3, 0, x_2);
return x_3;
}
}
static lean_object* _init_l_LeanCpOs_decodeTask___closed__3() {
_start:
{
uint8_t x_1; lean_object* x_2; lean_object* x_3; 
x_1 = 0;
x_2 = lean_box(x_1);
x_3 = lean_alloc_ctor(1, 1, 0);
lean_ctor_set(x_3, 0, x_2);
return x_3;
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_decodeTask(lean_object* x_1) {
_start:
{
lean_object* x_2; uint8_t x_3; 
x_2 = lean_unsigned_to_nat(0u);
x_3 = lean_nat_dec_eq(x_1, x_2);
if (x_3 == 0)
{
lean_object* x_4; uint8_t x_5; 
x_4 = lean_unsigned_to_nat(1u);
x_5 = lean_nat_dec_eq(x_1, x_4);
if (x_5 == 0)
{
lean_object* x_6; uint8_t x_7; 
x_6 = lean_unsigned_to_nat(2u);
x_7 = lean_nat_dec_eq(x_1, x_6);
if (x_7 == 0)
{
lean_object* x_8; 
x_8 = lean_box(0);
return x_8;
}
else
{
lean_object* x_9; 
x_9 = l_LeanCpOs_decodeTask___closed__1;
return x_9;
}
}
else
{
lean_object* x_10; 
x_10 = l_LeanCpOs_decodeTask___closed__2;
return x_10;
}
}
else
{
lean_object* x_11; 
x_11 = l_LeanCpOs_decodeTask___closed__3;
return x_11;
}
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_decodeTask___boxed(lean_object* x_1) {
_start:
{
lean_object* x_2; 
x_2 = l_LeanCpOs_decodeTask(x_1);
lean_dec(x_1);
return x_2;
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_taskCode(lean_object* x_1) {
_start:
{
if (lean_obj_tag(x_1) == 0)
{
lean_object* x_2; 
x_2 = lean_unsigned_to_nat(0u);
return x_2;
}
else
{
lean_object* x_3; uint8_t x_4; 
x_3 = lean_ctor_get(x_1, 0);
x_4 = lean_unbox(x_3);
switch (x_4) {
case 0:
{
lean_object* x_5; 
x_5 = lean_unsigned_to_nat(1u);
return x_5;
}
case 1:
{
lean_object* x_6; 
x_6 = lean_unsigned_to_nat(2u);
return x_6;
}
default: 
{
lean_object* x_7; 
x_7 = lean_unsigned_to_nat(3u);
return x_7;
}
}
}
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_taskCode___boxed(lean_object* x_1) {
_start:
{
lean_object* x_2; 
x_2 = l_LeanCpOs_taskCode(x_1);
lean_dec(x_1);
return x_2;
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_statusCode(uint8_t x_1) {
_start:
{
switch (x_1) {
case 0:
{
lean_object* x_2; 
x_2 = lean_unsigned_to_nat(0u);
return x_2;
}
case 1:
{
lean_object* x_3; 
x_3 = lean_unsigned_to_nat(1u);
return x_3;
}
case 2:
{
lean_object* x_4; 
x_4 = lean_unsigned_to_nat(2u);
return x_4;
}
case 3:
{
lean_object* x_5; 
x_5 = lean_unsigned_to_nat(3u);
return x_5;
}
default: 
{
lean_object* x_6; 
x_6 = lean_unsigned_to_nat(4u);
return x_6;
}
}
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_statusCode___boxed(lean_object* x_1) {
_start:
{
uint8_t x_2; lean_object* x_3; 
x_2 = lean_unbox(x_1);
lean_dec(x_1);
x_3 = l_LeanCpOs_statusCode(x_2);
return x_3;
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_stateCode(lean_object* x_1) {
_start:
{
if (lean_obj_tag(x_1) == 0)
{
lean_object* x_2; 
x_2 = lean_unsigned_to_nat(0u);
return x_2;
}
else
{
lean_object* x_3; uint8_t x_4; 
x_3 = lean_ctor_get(x_1, 0);
x_4 = lean_unbox(x_3);
switch (x_4) {
case 0:
{
lean_object* x_5; 
x_5 = lean_unsigned_to_nat(1u);
return x_5;
}
case 1:
{
lean_object* x_6; 
x_6 = lean_unsigned_to_nat(2u);
return x_6;
}
default: 
{
lean_object* x_7; 
x_7 = lean_unsigned_to_nat(3u);
return x_7;
}
}
}
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_stateCode___boxed(lean_object* x_1) {
_start:
{
lean_object* x_2; 
x_2 = l_LeanCpOs_stateCode(x_1);
lean_dec(x_1);
return x_2;
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_fromMask(lean_object* x_1) {
_start:
{
lean_object* x_2; lean_object* x_3; lean_object* x_4; uint8_t x_5; lean_object* x_6; lean_object* x_7; uint8_t x_8; lean_object* x_9; lean_object* x_10; lean_object* x_11; uint8_t x_12; lean_object* x_13; lean_object* x_14; 
x_2 = lean_unsigned_to_nat(2u);
x_3 = lean_nat_mod(x_1, x_2);
x_4 = lean_unsigned_to_nat(1u);
x_5 = lean_nat_dec_eq(x_3, x_4);
lean_dec(x_3);
x_6 = lean_nat_div(x_1, x_2);
x_7 = lean_nat_mod(x_6, x_2);
lean_dec(x_6);
x_8 = lean_nat_dec_eq(x_7, x_4);
lean_dec(x_7);
x_9 = lean_unsigned_to_nat(4u);
x_10 = lean_nat_div(x_1, x_9);
x_11 = lean_nat_mod(x_10, x_2);
lean_dec(x_10);
x_12 = lean_nat_dec_eq(x_11, x_4);
lean_dec(x_11);
x_13 = lean_alloc_ctor(0, 0, 3);
lean_ctor_set_uint8(x_13, 0, x_5);
lean_ctor_set_uint8(x_13, 1, x_8);
lean_ctor_set_uint8(x_13, 2, x_12);
x_14 = l_LeanCpOs_schedule(x_13);
return x_14;
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_fromMask___boxed(lean_object* x_1) {
_start:
{
lean_object* x_2; 
x_2 = l_LeanCpOs_fromMask(x_1);
lean_dec(x_1);
return x_2;
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_toMask(lean_object* x_1) {
_start:
{
uint8_t x_2; 
x_2 = lean_ctor_get_uint8(x_1, 0);
if (x_2 == 0)
{
uint8_t x_3; 
x_3 = lean_ctor_get_uint8(x_1, 1);
if (x_3 == 0)
{
uint8_t x_4; 
x_4 = lean_ctor_get_uint8(x_1, 2);
if (x_4 == 0)
{
lean_object* x_5; 
x_5 = lean_unsigned_to_nat(0u);
return x_5;
}
else
{
lean_object* x_6; 
x_6 = lean_unsigned_to_nat(4u);
return x_6;
}
}
else
{
uint8_t x_7; 
x_7 = lean_ctor_get_uint8(x_1, 2);
if (x_7 == 0)
{
lean_object* x_8; 
x_8 = lean_unsigned_to_nat(2u);
return x_8;
}
else
{
lean_object* x_9; 
x_9 = lean_unsigned_to_nat(6u);
return x_9;
}
}
}
else
{
uint8_t x_10; 
x_10 = lean_ctor_get_uint8(x_1, 1);
if (x_10 == 0)
{
uint8_t x_11; 
x_11 = lean_ctor_get_uint8(x_1, 2);
if (x_11 == 0)
{
lean_object* x_12; 
x_12 = lean_unsigned_to_nat(1u);
return x_12;
}
else
{
lean_object* x_13; 
x_13 = lean_unsigned_to_nat(5u);
return x_13;
}
}
else
{
uint8_t x_14; 
x_14 = lean_ctor_get_uint8(x_1, 2);
if (x_14 == 0)
{
lean_object* x_15; 
x_15 = lean_unsigned_to_nat(3u);
return x_15;
}
else
{
lean_object* x_16; 
x_16 = lean_unsigned_to_nat(7u);
return x_16;
}
}
}
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_toMask___boxed(lean_object* x_1) {
_start:
{
lean_object* x_2; 
x_2 = l_LeanCpOs_toMask(x_1);
lean_dec(x_1);
return x_2;
}
}
LEAN_EXPORT uint64_t l_LeanCpOs_pack(lean_object* x_1, uint8_t x_2, uint8_t x_3, lean_object* x_4) {
_start:
{
lean_object* x_5; lean_object* x_6; lean_object* x_7; lean_object* x_8; lean_object* x_9; lean_object* x_10; lean_object* x_11; lean_object* x_12; lean_object* x_13; lean_object* x_14; lean_object* x_15; lean_object* x_16; lean_object* x_17; 
x_5 = lean_ctor_get(x_1, 0);
x_6 = l_LeanCpOs_toMask(x_5);
x_7 = lean_ctor_get(x_1, 1);
x_8 = l_LeanCpOs_taskCode(x_7);
x_9 = lean_unsigned_to_nat(16u);
x_10 = lean_nat_mul(x_9, x_8);
lean_dec(x_8);
x_11 = lean_nat_add(x_6, x_10);
lean_dec(x_10);
lean_dec(x_6);
x_12 = l_LeanCpOs_statusCode(x_2);
x_13 = lean_unsigned_to_nat(256u);
x_14 = lean_nat_mul(x_13, x_12);
lean_dec(x_12);
x_15 = lean_nat_add(x_11, x_14);
lean_dec(x_14);
lean_dec(x_11);
x_16 = lean_unsigned_to_nat(65536u);
x_17 = lean_nat_mul(x_16, x_4);
if (x_3 == 0)
{
lean_object* x_18; lean_object* x_19; lean_object* x_20; uint64_t x_21; 
x_18 = lean_unsigned_to_nat(0u);
x_19 = lean_nat_add(x_15, x_18);
lean_dec(x_15);
x_20 = lean_nat_add(x_19, x_17);
lean_dec(x_17);
lean_dec(x_19);
x_21 = lean_uint64_of_nat(x_20);
lean_dec(x_20);
return x_21;
}
else
{
lean_object* x_22; lean_object* x_23; lean_object* x_24; uint64_t x_25; 
x_22 = lean_unsigned_to_nat(4096u);
x_23 = lean_nat_add(x_15, x_22);
lean_dec(x_15);
x_24 = lean_nat_add(x_23, x_17);
lean_dec(x_17);
lean_dec(x_23);
x_25 = lean_uint64_of_nat(x_24);
lean_dec(x_24);
return x_25;
}
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_pack___boxed(lean_object* x_1, lean_object* x_2, lean_object* x_3, lean_object* x_4) {
_start:
{
uint8_t x_5; uint8_t x_6; uint64_t x_7; lean_object* x_8; 
x_5 = lean_unbox(x_2);
lean_dec(x_2);
x_6 = lean_unbox(x_3);
lean_dec(x_3);
x_7 = l_LeanCpOs_pack(x_1, x_5, x_6, x_4);
lean_dec(x_4);
lean_dec(x_1);
x_8 = lean_box_uint64(x_7);
return x_8;
}
}
LEAN_EXPORT uint64_t l_LeanCpOs_packResult(lean_object* x_1) {
_start:
{
lean_object* x_2; 
x_2 = lean_ctor_get(x_1, 1);
if (lean_obj_tag(x_2) == 0)
{
uint8_t x_3; lean_object* x_4; uint8_t x_5; lean_object* x_6; uint64_t x_7; 
x_3 = lean_ctor_get_uint8(x_2, 0);
x_4 = lean_ctor_get(x_1, 0);
x_5 = 0;
x_6 = lean_unsigned_to_nat(0u);
x_7 = l_LeanCpOs_pack(x_4, x_3, x_5, x_6);
return x_7;
}
else
{
lean_object* x_8; uint8_t x_9; uint8_t x_10; lean_object* x_11; uint64_t x_12; 
x_8 = lean_ctor_get(x_1, 0);
x_9 = 0;
x_10 = 1;
x_11 = lean_unsigned_to_nat(0u);
x_12 = l_LeanCpOs_pack(x_8, x_9, x_10, x_11);
return x_12;
}
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_packResult___boxed(lean_object* x_1) {
_start:
{
uint64_t x_2; lean_object* x_3; 
x_2 = l_LeanCpOs_packResult(x_1);
lean_dec(x_1);
x_3 = lean_box_uint64(x_2);
return x_3;
}
}
static uint64_t _init_l_LeanCpOs_step___closed__1() {
_start:
{
lean_object* x_1; uint8_t x_2; uint8_t x_3; lean_object* x_4; uint64_t x_5; 
x_1 = l_LeanCpOs_initial;
x_2 = 4;
x_3 = 0;
x_4 = lean_unsigned_to_nat(0u);
x_5 = l_LeanCpOs_pack(x_1, x_2, x_3, x_4);
return x_5;
}
}
LEAN_EXPORT uint64_t lean_cp_step(uint32_t x_1, uint32_t x_2, uint32_t x_3) {
_start:
{
lean_object* x_4; lean_object* x_5; lean_object* x_6; uint8_t x_7; 
x_4 = lean_uint32_to_nat(x_1);
x_5 = l_LeanCpOs_fromMask(x_4);
x_6 = lean_unsigned_to_nat(8u);
x_7 = lean_nat_dec_le(x_6, x_4);
lean_dec(x_4);
if (x_7 == 0)
{
lean_object* x_8; lean_object* x_9; uint8_t x_10; 
x_8 = lean_uint32_to_nat(x_2);
x_9 = lean_unsigned_to_nat(0u);
x_10 = lean_nat_dec_eq(x_8, x_9);
if (x_10 == 0)
{
lean_object* x_11; uint8_t x_12; 
x_11 = lean_unsigned_to_nat(1u);
x_12 = lean_nat_dec_eq(x_8, x_11);
if (x_12 == 0)
{
lean_object* x_13; uint8_t x_14; 
x_13 = lean_unsigned_to_nat(2u);
x_14 = lean_nat_dec_eq(x_8, x_13);
if (x_14 == 0)
{
lean_object* x_15; uint8_t x_16; 
x_15 = lean_unsigned_to_nat(3u);
x_16 = lean_nat_dec_eq(x_8, x_15);
lean_dec(x_8);
if (x_16 == 0)
{
uint8_t x_17; uint8_t x_18; uint64_t x_19; 
x_17 = 4;
x_18 = 0;
x_19 = l_LeanCpOs_pack(x_5, x_17, x_18, x_9);
lean_dec(x_5);
return x_19;
}
else
{
lean_object* x_20; lean_object* x_21; lean_object* x_22; lean_object* x_23; lean_object* x_24; lean_object* x_25; uint8_t x_26; uint8_t x_27; uint64_t x_28; 
x_20 = lean_uint32_to_nat(x_3);
x_21 = l_LeanCpOs_decodeTask(x_20);
lean_dec(x_20);
lean_inc(x_5);
x_22 = l_LeanCpOs_getTaskState(x_5, x_21);
x_23 = lean_ctor_get(x_22, 0);
lean_inc(x_23);
x_24 = lean_ctor_get(x_22, 1);
lean_inc(x_24);
lean_dec(x_22);
x_25 = l_LeanCpOs_stateCode(x_24);
lean_dec(x_24);
x_26 = 0;
x_27 = lean_unbox(x_23);
lean_dec(x_23);
x_28 = l_LeanCpOs_pack(x_5, x_27, x_26, x_25);
lean_dec(x_25);
lean_dec(x_5);
return x_28;
}
}
else
{
lean_object* x_29; lean_object* x_30; lean_object* x_31; lean_object* x_32; uint8_t x_33; uint8_t x_34; uint64_t x_35; 
lean_dec(x_8);
lean_inc(x_5);
x_29 = l_LeanCpOs_getTaskID(x_5);
x_30 = lean_ctor_get(x_29, 0);
lean_inc(x_30);
x_31 = lean_ctor_get(x_29, 1);
lean_inc(x_31);
lean_dec(x_29);
x_32 = l_LeanCpOs_taskCode(x_31);
lean_dec(x_31);
x_33 = 0;
x_34 = lean_unbox(x_30);
lean_dec(x_30);
x_35 = l_LeanCpOs_pack(x_5, x_34, x_33, x_32);
lean_dec(x_32);
lean_dec(x_5);
return x_35;
}
}
else
{
lean_object* x_36; uint64_t x_37; 
lean_dec(x_8);
x_36 = l_LeanCpOs_terminate(x_5);
x_37 = l_LeanCpOs_packResult(x_36);
lean_dec(x_36);
return x_37;
}
}
else
{
lean_object* x_38; lean_object* x_39; lean_object* x_40; uint64_t x_41; 
lean_dec(x_8);
x_38 = lean_uint32_to_nat(x_3);
x_39 = l_LeanCpOs_decodeTask(x_38);
lean_dec(x_38);
x_40 = l_LeanCpOs_activate(x_5, x_39);
x_41 = l_LeanCpOs_packResult(x_40);
lean_dec(x_40);
return x_41;
}
}
else
{
uint64_t x_42; 
lean_dec(x_5);
x_42 = l_LeanCpOs_step___closed__1;
return x_42;
}
}
}
LEAN_EXPORT lean_object* l_LeanCpOs_step___boxed(lean_object* x_1, lean_object* x_2, lean_object* x_3) {
_start:
{
uint32_t x_4; uint32_t x_5; uint32_t x_6; uint64_t x_7; lean_object* x_8; 
x_4 = lean_unbox_uint32(x_1);
lean_dec(x_1);
x_5 = lean_unbox_uint32(x_2);
lean_dec(x_2);
x_6 = lean_unbox_uint32(x_3);
lean_dec(x_3);
x_7 = lean_cp_step(x_4, x_5, x_6);
x_8 = lean_box_uint64(x_7);
return x_8;
}
}
lean_object* initialize_Init(uint8_t builtin, lean_object*);
lean_object* initialize_LeanCpOs_Model(uint8_t builtin, lean_object*);
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_LeanCpOs_Bridge(uint8_t builtin, lean_object* w) {
lean_object * res;
if (_G_initialized) return lean_io_result_mk_ok(lean_box(0));
_G_initialized = true;
res = initialize_Init(builtin, lean_io_mk_world());
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_LeanCpOs_Model(builtin, lean_io_mk_world());
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
l_LeanCpOs_decodeTask___closed__1 = _init_l_LeanCpOs_decodeTask___closed__1();
lean_mark_persistent(l_LeanCpOs_decodeTask___closed__1);
l_LeanCpOs_decodeTask___closed__2 = _init_l_LeanCpOs_decodeTask___closed__2();
lean_mark_persistent(l_LeanCpOs_decodeTask___closed__2);
l_LeanCpOs_decodeTask___closed__3 = _init_l_LeanCpOs_decodeTask___closed__3();
lean_mark_persistent(l_LeanCpOs_decodeTask___closed__3);
l_LeanCpOs_step___closed__1 = _init_l_LeanCpOs_step___closed__1();
return lean_io_result_mk_ok(lean_box(0));
}
#ifdef __cplusplus
}
#endif
