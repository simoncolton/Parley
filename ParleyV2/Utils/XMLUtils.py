from xml.dom import minidom

class XMLUtils:

    def open_xml_doc(file_path):
        dom = minidom.parse(file_path)
        return dom

    def get_doc_and_root(elem_name, attributes_dict={}):
        docu = minidom.parseString(f"<{elem_name}/>")
        root_elem = docu.documentElement
        XMLUtils.set_attributes(root_elem, attributes_dict)
        return docu, root_elem

    def set_attributes(elem, attributes_dict):
        for key in attributes_dict.keys():
            elem.setAttribute(key, attributes_dict[key])

    def add_child(docu, elem, child_name, attributes_dict={}, child_text=None):
        child_elem = docu.createElement(child_name)
        XMLUtils.set_attributes(child_elem, attributes_dict)
        elem.appendChild(child_elem)
        if child_text is not None:
            child_text_elem = docu.createTextNode(child_text)
            child_elem.appendChild(child_text_elem)
        return child_elem

    def prettify(docu):
        return docu.toprettyxml()

