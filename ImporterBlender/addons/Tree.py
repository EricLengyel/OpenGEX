
class TreeBase:
    def __init__(self):
        self.prev_node = None
        self.next_node = None
        self.super_node = None
        self.first_sub_node = None
        self.last_sub_node = None

    def get_root_node(self):
        root = self
        while True:
            if not root.super_node:
                break;
            root = root.super_node

        return root

    def successor(self, node):
        node_super = node.super_node
        while node_super:
            if node_super == self:
                return True

            node_super = node_super.super_node

        return False

    def get_left_most_node(self):
        node = self
        while True:
            sub_node = node.first_sub_node
            if not sub_node:
                break

            node = sub_node

        return node

    def get_right_most_node(self):
        node = self
        while True:
            sub_node = node.last_sub_node
            if not sub_node:
                break

            node = sub_node

        return node

    def get_next_tree_node(self, node):
        next_node = node.first_sub_node
        if not next_node:
            while True:
                if node == self:
                    break

                next_node = node.next_node
                if next_node:
                    break

                #This might be problematic is not a local pointer it's an actual reference
                node = node.super_node

        return next_node

    def get_previous_tree_node(self, node):
        if node == self:
            return None

        previous_node = node.prev_node
        if not previous_node:
            return node.super_node

        return node.get_right_most_node()

    def get_next_level_node(self, node):
        next_node = None
        while True:
            if node == self:
                break

            next_node = node.next_node
            if next_node:
                break

            #This might be problematic is not a local pointer it's an actual reference
            node = node.super_node

        return next_node

    def get_previous_level_node(self, node):
        previous_node = None
        while True:
            if node == self:
                break

            previous_node = node.prev_node
            if previous_node:
                break

            node = node.super_node

        return previous_node

    def get_sub_node_count(self):
        count = 0
        sub_node = self.first_sub_node
        while sub_node:
            count += 1
            sub_node = sub_node.next_node

        return count

    def get_sub_tree_node_count(self):
        count = 0
        sub_node = self.first_sub_node
        while sub_node:
            count += 1
            sub_node = self.get_next_tree_node(sub_node)

        return count

    def get_node_index(self):
        index = 0
        element = self
        while True:
            element = element.prev_node
            if not element:
                break

            index += 1

        return index

    def get_node_depth(self):
        depth = 0
        element = self
        while True:
            element = element.super_node
            if not element:
                break

            depth += 1

        return depth

    def move_sub_tree(self, super_node):
        while True:
            node = self.first_sub_node
            if not node:
                break

            super_node.append_sub_node(node)

    def remove_sub_tree(self):
        sub_node = self.first_sub_node
        while sub_node:
            next_node = sub_node.next_node
            sub_node.prev_node = None
            sub_node.next_node = None
            sub_node.super_node = None
            sub_node = next_node

        self.first_sub_node = None
        self.last_sub_node = None

    def purge_sub_tree(self):
        while self.first_sub_node:
            self.first_sub_node = None

    def append_sub_node(self, node):
        tree = node.super_node
        if tree:
            previous_node = node.prev_node
            next_node = node.next_node

            if previous_node:
                previous_node.next_node = next_node
                node.prev_node = None

            if next_node:
                next_node.prev_node = previous_node
                node.next_node = None

            if tree.first_sub_node == node:
                tree.first_sub_node = next_node

            if tree.last_sub_node == node:
                tree.last_sub_node = previous_node

        node.super_node = self

        if self.last_sub_node:
            self.last_sub_node.next_node = node
            node.prev_node = self.last_sub_node
            self.last_sub_node = node
        else:
            self.first_sub_node = node
            self.last_sub_node = node

    def prepend_sub_node(self, node):
        tree = node.super_node
        if tree:
            previous_node = node.prev_node
            next_node = node.next_node

            if previous_node:
                previous_node.next_node = next_node
                node.prev_node = None

            if next_node:
                next_node.prev_node = previous_node
                node.next_node = None

            if tree.first_sub_node == node:
                tree.first_sub_node = next_node

            if tree.last_sub_node == node:
                tree.last_sub_node = previous_node

        node.super_node = self

        if self.first_sub_node:
            self.first_sub_node.prev_node = node
            node.next_node = self.first_sub_node
            self.first_sub_node = node
        else:
            self.first_sub_node = node
            self.last_sub_node = node


    def insert_sub_node_before(self, node, before):
        tree = node.super_node
        if tree:
            previous_node = node.prev_node
            next_node = node.next_node

            if previous_node:
                previous_node.next_node = next_node

            if next_node:
                next_node.prev_node = previous_node

            if tree.first_sub_node == node:
                tree.first_sub_node = next_node

            if tree.last_sub_node == node:
                tree.last_sub_node = previous_node

        node.super_node = self
        node.next_node = before

        if before:
            after = before.prev_node
            node.prev_node = after
            before.prev_node = node

            if after:
                after.next_node = node
            else:
                self.first_sub_node = node
        else:
            after = self.last_sub_node
            node.prev_node = after

            if after:
                after.next_node = node
                self.last_sub_node = node
            else:
                self.first_sub_node = node
                self.last_sub_node = node

    def insert_sub_node_after(self, node, after):
        tree = node.super_node
        if tree:
            previous_node = node.prev_node
            next_node = node.next_node

            if previous_node:
                previous_node.next_node = next_node

            if next_node:
                next_node.prev_node = previous_node

            if tree.first_sub_node == node:
                tree.first_sub_node = next_node

            if tree.last_sub_node == node:
                tree.last_sub_node = previous_node

        node.super_node = self
        node.prev_node = after

        if after:
            before = after.next_node
            node.next_node = before
            after.next_node = node

            if before:
                before.prev_node = node
            else:
                self.last_sub_node = node
        else:
            before = self.first_sub_node
            node.next_node = before

            if before:
                before.prev_node = node
                self.first_sub_node = node
            else:
                self.first_sub_node = node
                self.last_sub_node = node

    def remove_sub_node(self, node):
        previous_node = node.prev_node
        next_node = node.next_node

        if previous_node:
            previous_node.next_node = next_node

        if next_node:
            next_node.prev_node = previous_node

        if self.first_sub_node == node:
            self.first_sub_node = next_node

        if self.last_sub_node == node:
            self.last_sub_node = previous_node

        node.prev_node = None
        node.next_node = None
        node.super_node = None

    def detach(self):
        if self.super_node:
            self.super_node.remove_sub_node(self)