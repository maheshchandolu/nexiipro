# data_list= [4,4,2,1]
# def reverse(data_list):
#     print("-----------2--------------------")
#     length = len(data_list)
#     s = length

#     new_list = [None]*length
#     print(new_list,"----------")
#     for item in data_list:
#         s = s - 1
#         new_list[s] = item
#         print(new_list[s],"-----------------item-")
#     return new_list
# reverse(data_list)



# a = [1,2,3,4]

# def reverse_the_list(a):
#    reversed_list = []
#    for i in range(0, len(a)):
#      reversed_list.append(a[len(a) - i - 1])
#    return reversed_list

# new_list = reverse_the_list(a)
# print (new_list)

ls = ['1a','2b','3c','4d',1,2]
for i in range(len(ls)):
    print(ls[-(i+1)])


# print(ls[-(i+1)])